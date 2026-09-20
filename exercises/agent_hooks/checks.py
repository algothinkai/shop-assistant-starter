"""Registered SDK callback contracts, not actual agent execution."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from shop_assistant.business import ShopService
from .adapter import build_options, content, REFUND, SHIPPING


class HookChecks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.shop = ShopService(Path(self.directory.name))
        self.audit = []
        self.options = build_options(self.shop, self.audit, "not-a-live-model")
        self.before = self.options.hooks["PreToolUse"][0].hooks[0]
        self.after = self.options.hooks["PostToolUse"][0].hooks[0]

    async def pre(self, **args):
        return await self.before({"hook_event_name": "PreToolUse", "tool_name": REFUND,
                                  "tool_input": {"order_id": "O-1003", "amount_cents": 7600, **args}}, "use-1", {})

    async def post(self, value):
        return await self.after({"hook_event_name": "PostToolUse", "tool_name": SHIPPING,
                                 "tool_response": value}, "use-2", {})

    async def test_unverified_and_threshold_are_denied_without_mutation(self):
        result = await self.pre()
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        self.shop.set_simulated_identity("C-1003", True)
        result = await self.pre(amount_cents=50001)
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("human", result["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(self.shop.ledger(), [])

    async def test_valid_preflight_does_not_override_permission_or_write_ledger(self):
        self.shop.set_simulated_identity("C-1003", True)
        self.assertEqual(await self.pre(), {})
        self.assertEqual(self.audit[-1]["decision"], "continue_permission_checks")
        self.assertEqual(self.shop.ledger(), [])
        self.shop.set_simulated_identity("C-1003", False)
        self.assertEqual((await self.pre())["hookSpecificOutput"]["permissionDecision"], "deny")

    async def test_wrong_case_and_malformed_amount_denied(self):
        self.shop.set_simulated_identity("C-1003", True)
        for args in ({"amount_cents": True}, {"amount_cents": "7600"}, {"amount_cents": 0}, {"order_id": "O-1002"}):
            self.assertEqual((await self.pre(**args))["hookSpecificOutput"]["permissionDecision"], "deny")

    async def test_equivalent_carrier_formats_normalize_without_mutation(self):
        outputs = []
        for value in ({"timestamp": 1788220800, "status": 20},
                      {"timestamp": "2026-09-01T01:00:00+01:00", "status": "delivered"}):
            wrapped = content(value)
            original = copy.deepcopy(wrapped)
            result = await self.post(wrapped)
            replacement = result["hookSpecificOutput"]["updatedToolOutput"]
            self.assertFalse(replacement["isError"])
            outputs.append(json.loads(replacement["content"][0]["text"]))
            self.assertEqual(wrapped, original)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0]["timestamp_utc"], "2026-09-01T00:00:00Z")
        self.assertEqual(outputs[0]["status"], "delivered")

    async def test_invalid_carrier_data_stays_explicit_failure(self):
        for value in ({"timestamp": "2026-09-01T00:00:00", "status": 20},
                      {"timestamp": True, "status": 20}, {"timestamp": 1788220800, "status": 999},
                      {"timestamp": float("inf"), "status": 20}, {"timestamp": 0, "status": True}):
            result = await self.post(content(value))
            self.assertTrue(result["hookSpecificOutput"]["updatedToolOutput"]["isError"])
        self.assertTrue((await self.post({"content": []}))["hookSpecificOutput"]["updatedToolOutput"]["isError"])

    async def test_existing_tool_error_is_not_rewritten_as_success(self):
        response = content({"code": "CARRIER_UNAVAILABLE"}, error=True)
        self.assertEqual(await self.post(response), {})
        self.assertEqual(self.audit[-1]["normalization"], "preserved_error")

    async def test_unrelated_events_and_tools_are_unchanged(self):
        for callback in (self.before, self.after):
            self.assertEqual(await callback({"hook_event_name": "Other", "tool_name": "mcp__other__shipping_sample"}, "u", {}), {})
        self.assertEqual(self.audit, [])

    async def test_registration_is_bounded_and_keeps_host_settings_disabled(self):
        self.assertEqual(self.options.tools, [])
        self.assertEqual(self.options.setting_sources, [])
        self.assertTrue(self.options.strict_mcp_config)
        self.assertEqual(self.options.allowed_tools, [REFUND, SHIPPING])
        self.assertEqual(set(self.options.mcp_servers), {"shop"})
        self.assertEqual(self.options.max_turns, 4)
        self.assertEqual(self.options.max_budget_usd, 0.10)
        self.assertNotEqual(self.options.permission_mode, "bypassPermissions")


class RuntimeBoundaryChecks(unittest.IsolatedAsyncioTestCase):
    async def test_error_missing_and_success_terminal_are_distinct(self):
        import contextlib
        import io
        from unittest.mock import patch
        from claude_agent_sdk import ResultMessage
        from . import demo
        for kind, expected in (("error_max_turns", 1), ("missing", 1), ("success", 0)):
            class Client:
                def __init__(self, options):
                    self.options = options
                async def __aenter__(self):
                    return self
                async def __aexit__(self, *args):
                    return False
                async def query(self, prompt):
                    return None
                async def receive_response(self):
                    await self.options.hooks["PreToolUse"][0].hooks[0]({"hook_event_name": "PreToolUse", "tool_name": REFUND, "tool_input": {"order_id": "O-1003", "amount_cents": 7600}}, "r", {})
                    await self.options.hooks["PostToolUse"][0].hooks[0]({"hook_event_name": "PostToolUse", "tool_name": SHIPPING, "tool_response": content({"timestamp": 1788220800, "status": 20})}, "s", {})
                    if kind != "missing":
                        yield ResultMessage(subtype=kind, is_error=kind != "success", duration_ms=1, duration_api_ms=1, num_turns=1, session_id="synthetic", errors=["PRIVATE_DIAGNOSTIC"], result="PRIVATE_RESULT")
            output = io.StringIO()
            with patch.object(demo, "ClaudeSDKClient", Client), patch.dict("os.environ", {"ANTHROPIC_MODEL": "test-no-network"}), contextlib.redirect_stdout(output):
                code = await demo.run(True)
            self.assertEqual(code, expected)
            data = json.loads(output.getvalue())
            self.assertTrue(data["hooks_observed"])
            self.assertEqual(data["status"], "OBSERVED_REQUESTED_HOOKS" if expected == 0 else "UNVERIFIED")
            self.assertNotIn("PRIVATE_", output.getvalue())

    async def test_real_sdk_transport_does_not_inherit_raw_cli_stderr(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as directory:
            cli = Path(directory) / "fake-cli"
            cli.write_text("#!/bin/sh\necho SYNTHETIC_PRIVATE_DIAGNOSTIC >&2\nexit 1\n")
            cli.chmod(0o700)
            code = """import asyncio,sys,tempfile
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient
from shop_assistant.business import ShopService
from exercises.agent_hooks.adapter import build_options
async def run():
    with tempfile.TemporaryDirectory() as directory:
        options=build_options(ShopService(Path(directory)), [], 'no-model')
        options.cli_path=sys.argv[1]
        try:
            async with ClaudeSDKClient(options=options): pass
        except Exception: pass
asyncio.run(run())
"""
            out = subprocess.run([sys.executable, "-c", code, str(cli)], capture_output=True, text=True, timeout=15)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertNotIn("SYNTHETIC_PRIVATE_DIAGNOSTIC", out.stdout + out.stderr)
