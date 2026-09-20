import json
import tempfile
import unittest
from claude_agent_sdk import AssistantMessage, ToolUseBlock
from .adapter import build_options, consume
from .runtime import ResearchRuntime, PREFIX
from .fixtures import authored_stream, call_hook, terminal


class CoordinatorChecks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.runtime = ResearchRuntime(["returns", "shipping"])
        self.options = build_options(self.runtime, self.directory.name, "offline-model")

    async def test_options_limit_tools_settings_depth_and_cost(self):
        self.assertEqual(self.options.tools, ["Agent"])
        self.assertEqual(self.options.setting_sources, [])
        self.assertTrue(self.options.strict_mcp_config)
        self.assertEqual(self.options.env["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"], "1")
        self.assertEqual(self.options.env["CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS"], "2")
        self.assertEqual(
            self.options.env["CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS"], "1"
        )
        self.assertEqual(self.options.max_budget_usd, 0.50)
        for agent in self.options.agents.values():
            self.assertEqual(agent.tools, [PREFIX + "investigate"])

    async def test_delegation_injects_complete_prior_context_and_dates(self):
        self.runtime.investigate("returns", self.runtime.scope("returns")[:1])
        before = self.runtime.reports["returns"]
        result = await call_hook(
            self.options,
            "Agent",
            {"subagent_type": "returns-research", "prompt": "Fill evidence gaps"},
            "d1",
        )
        payload = json.loads(result["updatedInput"]["prompt"])
        self.assertEqual(payload["prior_report"], before)
        self.assertEqual(payload["as_of"], self.runtime.as_of)
        self.assertEqual(
            payload["coverage"]["missing_sources"],
            ["FAQ-RETURNS-2026-09", "POL-RETURN-2026-09"],
        )
        self.assertFalse(result["updatedInput"]["run_in_background"])

    async def test_wrong_topic_root_reads_and_recursive_delegation_are_denied(self):
        for name, args, role in [
            (PREFIX + "investigate", {"topic": "returns", "source_ids": []}, None),
            (
                PREFIX + "investigate",
                {"topic": "shipping", "source_ids": []},
                "returns-research",
            ),
            (
                "Agent",
                {"subagent_type": "shipping-research", "prompt": "nested"},
                "returns-research",
            ),
            ("Agent", {"subagent_type": "general-purpose", "prompt": "unknown"}, None),
            ("Bash", {"command": "pwd"}, None),
            (PREFIX + "inspect_coverage", {}, "returns-research"),
        ]:
            self.assertEqual(
                (await call_hook(self.options, name, args, "bad", role))[
                    "permissionDecision"
                ],
                "deny",
            )

    async def test_partial_failure_keeps_healthy_sibling_and_full_attempts(self):
        runtime = ResearchRuntime(["returns", "shipping"], fault="persistent")
        options = build_options(runtime, self.directory.name, "offline-model")
        result = await consume(authored_stream(runtime, options), runtime)
        self.assertEqual(result["status"], "observed_workflow")
        self.assertEqual(
            result["coverage"]["topics"]["shipping"]["coverage"], "supported"
        )
        self.assertEqual(
            result["coverage"]["topics"]["returns"]["coverage"], "partial_failure"
        )
        self.assertFalse(result["coverage"]["ready"])
        attempts = [
            e
            for e in runtime.events
            if e["event"] == "source_read" and e["source_id"] == "FAQ-RETURNS-2026-09"
        ][0]["attempts"]
        self.assertEqual(len(attempts), 2)

    async def test_gap_driven_follow_up_preserves_conflicts_and_records_parallel_batch(
        self,
    ):
        result = await consume(
            authored_stream(self.runtime, self.options), self.runtime
        )
        self.assertEqual(result["status"], "observed_workflow")
        self.assertTrue(result["parallel_call_batch_observed"])
        self.assertEqual(result["delegated_topics"], ["returns", "shipping", "returns"])
        self.assertEqual(
            result["coverage"]["topics"]["returns"]["coverage"], "contested"
        )
        self.assertEqual(len(result["coverage"]["topics"]["returns"]["claims"]), 2)
        self.assertEqual(
            len(
                [
                    e
                    for e in self.runtime.events
                    if e["event"] == "report" and e["topic"] == "shipping"
                ]
            ),
            1,
        )

    async def test_single_topic_does_not_run_unrequested_pipeline(self):
        runtime = ResearchRuntime(["shipping"])
        options = build_options(runtime, self.directory.name, "offline-model")
        self.assertEqual(set(options.agents), {"shipping-research"})
        result = await consume(authored_stream(runtime, options), runtime)
        self.assertEqual(result["delegated_topics"], ["shipping"])
        self.assertTrue(result["coverage"]["ready"])
        self.assertFalse(result["parallel_call_batch_observed"])

    async def test_transient_failure_recovers_locally_before_propagating(self):
        runtime = ResearchRuntime(["returns"], fault="transient")
        result = runtime.investigate("returns", runtime.scope("returns"))
        self.assertEqual(result["report"]["status"], "ok")
        reads = result["read_attempts"][-1]["attempts"]
        self.assertEqual([a["outcome"] for a in reads], ["timeout", "ok"])

    async def test_terminal_text_alone_cannot_prove_delegation(self):
        async def stream():
            yield terminal()

        self.assertEqual(
            (await consume(stream(), self.runtime))["status"], "unverified"
        )

    async def test_abnormal_missing_duplicate_and_exception_terminal_fail(self):
        for mode in ["error", "missing", "duplicate", "exception"]:
            runtime = ResearchRuntime(["shipping"])
            options = build_options(runtime, self.directory.name, "offline-model")

            async def stream():
                async for message in authored_stream(runtime, options):
                    if isinstance(message, type(terminal())):
                        if mode == "missing":
                            continue
                        yield terminal(True) if mode == "error" else message
                        if mode == "duplicate":
                            yield message
                        if mode == "exception":
                            raise RuntimeError("untrusted transport text")
                    else:
                        yield message

            self.assertEqual((await consume(stream(), runtime))["status"], "unverified")

    async def test_unrelated_child_result_cannot_prove_requested_work(self):
        async def stream():
            async for message in authored_stream(self.runtime, self.options):
                if isinstance(message, AssistantMessage) and message.parent_tool_use_id:
                    message.parent_tool_use_id = "unknown"
                yield message

        self.assertEqual(
            (await consume(stream(), self.runtime))["status"], "unverified"
        )

    async def test_stale_coverage_cannot_count_as_final_inspection(self):
        async def stream():
            async for message in authored_stream(self.runtime, self.options):
                if isinstance(message, type(terminal())):
                    self.runtime.investigate("shipping", [])
                yield message

        self.assertEqual(
            (await consume(stream(), self.runtime))["status"], "unverified"
        )

    async def test_invalid_scope_mcp_error_does_not_mutate_reports(self):
        result = await self.runtime.handlers["investigate"](
            {"topic": "returns", "source_ids": ["POL-SHIP-2026-06"]}
        )
        self.assertTrue(result["isError"])
        self.assertEqual(self.runtime.reports, {})
