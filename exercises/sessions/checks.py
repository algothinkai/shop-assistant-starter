"""Session contract checks instantiate real pinned SDK types; no live model."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from claude_agent_sdk import ClaudeAgentOptions
from .adapter import choose_action, build_options, consume
from .fixtures import result, authored_query, PARENT, CHILD
from .probe import probe


async def stream(*messages):
    for m in messages: yield m


class SessionChecks(unittest.IsolatedAsyncioTestCase):
    def test_explicit_mode_and_source_freshness(self):
        for mode in ["resume","fork"]:
            self.assertEqual(choose_action(mode,PARENT,{"file":"v1"},{"file":"v1"}),mode)
            self.assertEqual(choose_action(mode,PARENT,{"file":"v1"},{"file":"v2"}),"fresh")
            self.assertEqual(choose_action(mode,PARENT,{"file":"v1"},{"other":"v1"}),"fresh")
        self.assertEqual(choose_action("fresh",None,{}, {"file":"v1"}),"fresh")
        with self.assertRaises(ValueError):choose_action("resume",None,{"file":"v1"},{"file":"v1"})

    def test_builds_real_sdk_options_without_implicit_recent_session(self):
        with tempfile.TemporaryDirectory() as d:
            for action in ["fresh","resume","fork"]:
                options=build_options(action,None if action=="fresh" else PARENT,d,"offline-model")
                self.assertIsInstance(options,ClaudeAgentOptions)
                self.assertFalse(options.continue_conversation)
                self.assertEqual(options.resume,None if action=="fresh" else PARENT)
                self.assertEqual(options.fork_session,action=="fork")
                self.assertEqual(options.tools,[])
                self.assertEqual(options.setting_sources,[])
                self.assertTrue(options.strict_mcp_config)
                self.assertEqual(options.mcp_servers,{})
                self.assertEqual(options.max_turns,2)
                self.assertEqual(options.max_budget_usd,0.10)
                self.assertIsNotNone(options.stderr)

    def test_invalid_inputs_never_dispatch(self):
        with tempfile.TemporaryDirectory() as d:
            for action,sid,model in [("latest",PARENT,"model"),("resume","bad","model"),("fork",None,"model"),("fresh",None,"")]:
                with self.assertRaises(ValueError):build_options(action,sid,d,model)

    async def test_only_terminal_success_is_success(self):
        self.assertEqual((await consume(stream(result(text="ok"))))["status"],"success")
        for terminal in [result(subtype="error_max_turns"),result(stop_reason="max_tokens"),result(terminal_reason="error_max_budget_usd")]:
            outcome=await consume(stream(terminal))
            self.assertEqual(outcome["status"],"failed")
            self.assertEqual(outcome["session_id"],PARENT)
            self.assertIsNone(outcome["text"])

    async def test_missing_duplicate_invalid_terminal_fail(self):
        for items in [[],[result(),result()],[result(sid="not-an-id")]]:
            self.assertEqual((await consume(stream(*items)))["status"],"failed")

    async def test_exception_after_terminal_is_failure_without_leaked_detail(self):
        async def failing():
            yield result(text="PRIVATE OUTPUT")
            raise RuntimeError("PRIVATE CREDENTIAL")
        outcome=await consume(failing())
        self.assertEqual(outcome["status"],"failed")
        self.assertNotIn("PRIVATE",str(outcome))
        self.assertEqual(outcome["session_id"],PARENT)

    async def test_cancellation_is_not_swallowed(self):
        async def cancelled():
            raise asyncio.CancelledError()
            yield
        with self.assertRaises(asyncio.CancelledError):await consume(cancelled())

    async def test_authored_four_turn_probe_checks_parent_after_fork(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[];authored=authored_query()
            def recording(**kwargs):
                calls.append(kwargs);return authored(**kwargs)
            outcome=await probe(recording,d,"offline-model")
            self.assertEqual(outcome["status"],"observed_sequence")
            self.assertEqual([c["options"].resume for c in calls],[None,PARENT,PARENT,PARENT])
            self.assertTrue(calls[2]["options"].fork_session)
            self.assertNotIn("7600",calls[1]["prompt"])
            self.assertNotIn("7600",calls[3]["prompt"])

    async def test_wrong_fork_id_or_changed_parent_cannot_pass(self):
        for wrong_step in [3,4]:
            count=0
            async def wrong(*,prompt,options):
                nonlocal count
                count+=1
                import json
                sid=PARENT if count!=3 or wrong_step==3 else CHILD
                amount=7500 if count==3 or (count==4 and wrong_step==4) else 7600
                yield result(sid,text=json.dumps({"case_code":"training-cobalt","amount_cents":amount}))
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual((await probe(wrong,d,"offline-model"))["status"],"unverified")

    async def test_failure_stops_without_automatic_retry(self):
        calls=[]
        async def failing(**kwargs):
            calls.append(kwargs);yield result(subtype="error_max_budget_usd")
        with tempfile.TemporaryDirectory() as d:
            outcome=await probe(failing,d,"offline-model")
            self.assertEqual(len(calls),1)
            self.assertEqual(outcome["status"],"unverified")

    async def test_ambiguous_or_noninteger_facts_stop_probe(self):
        for text in ['{"case_code":"wrong","case_code":"training-cobalt","amount_cents":1,"amount_cents":7600}',
                     '{"case_code":"training-cobalt","amount_cents":7600.0}']:
            calls=[]
            async def ambiguous(**kwargs):
                calls.append(kwargs)
                yield result(text=text)
            with tempfile.TemporaryDirectory() as d:
                outcome=await probe(ambiguous,d,"offline-model")
                self.assertEqual(len(calls),1)
                self.assertFalse(outcome["trace"][0]["facts_match"])
                self.assertEqual(outcome["status"],"unverified")
