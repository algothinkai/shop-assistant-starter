"""Authored envelopes and actual local Python processes; no live model calls."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from exercises.code_review.fixtures import FILES, ISSUE
from exercises.code_review.workflow import ReviewFailure
from .adapter import command, context, decode, execute, run_pass


def envelope(host, findings=None):
    result = {"findings": findings if findings is not None else [deepcopy(ISSUE)]}
    if host == "claude":
        return (
            json.dumps(
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "structured_output": result,
                }
            ),
            None,
            0,
        )
    final = json.dumps(result)
    events = [
        {"type": "thread.started", "thread_id": "authored"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "authored-message", "type": "agent_message", "text": final},
        },
        {"type": "turn.completed", "usage": {}},
    ]
    return "\n".join(map(json.dumps, events)), final, 0


class HostChecks(unittest.TestCase):
    def test_context_has_tests_prior_and_scope_not_generator_history(self):
        text = context(FILES, "local:refund.py")
        self.assertIn("test_zero_refund", text)
        self.assertNotIn("def send_refund", text)
        payload = json.loads(text.split("CONTEXT_JSON\n")[1])
        self.assertEqual(payload["allowed_files"], ["refund.py"])
        self.assertIsNone(payload["prior_findings"])
        self.assertNotIn("generator_history", payload)

    def test_host_flags_use_fresh_noninteractive_schema_paths(self):
        with TemporaryDirectory() as d:
            a = command("claude", "/fake/claude", "chosen-model", d)
            b = command("codex", "/fake/codex", "chosen-model", d)
            self.assertIn("--bare", a)
            self.assertIn("-p", a)
            self.assertIn("--json-schema", a)
            self.assertEqual(a[a.index("--tools") + 1], "")
            self.assertIn("--output-schema", b)
            self.assertIn("--ephemeral", b)
            self.assertEqual(b[b.index("--sandbox") + 1], "read-only")
            self.assertNotIn("resume", a + b)
            self.assertNotIn("--continue", a + b)

    def test_both_valid_envelopes_bind_findings(self):
        for host in ("claude", "codex"):

            def fake(args, prompt, directory):
                return envelope(host)

            report = run_pass(
                host,
                "/fake/host",
                "chosen-model",
                FILES,
                "local:refund.py",
                executor=fake,
            )
            self.assertEqual(report["status"], "complete")
            self.assertEqual(report["findings"][0]["cause"], ISSUE["cause"])

    def test_nonzero_exit_never_becomes_clean_review(self):
        for host in ("claude", "codex"):
            out, final, _ = envelope(host, [])
            with self.assertRaisesRegex(ReviewFailure, "review_process_failed"):
                decode(host, out, final, 1)

    def test_claude_missing_schema_or_error_is_failure(self):
        for field, value in [
            ("is_error", True),
            ("subtype", "error_max_turns"),
            ("structured_output", None),
        ]:
            out, _, _ = envelope("claude", [])
            record = json.loads(out)
            record[field] = value
            with self.assertRaises(ReviewFailure):
                decode("claude", json.dumps(record), None, 0)

    def test_codex_requires_terminal_and_matching_final(self):
        out, final, _ = envelope("codex", [])
        for changed in [
            out.rsplit("\n", 1)[0],
            out + "\n" + json.dumps({"type": "error"}),
            out.replace("turn.started", "turn.failed"),
        ]:
            with self.assertRaises(ReviewFailure):
                decode("codex", changed, final, 0)
        with self.assertRaisesRegex(ReviewFailure, "final_output_mismatch"):
            decode("codex", out, json.dumps({"findings": [ISSUE]}), 0)

    def test_codex_unrequested_tools_or_invalid_event_rejected(self):
        out, final, _ = envelope("codex", [])
        events = out.splitlines()
        for item in [
            {"type": "item.completed", "item": {"type": "command_execution"}},
            {"type": []},
        ]:
            bad = "\n".join(events[:2] + [json.dumps(item)] + events[2:])
            with self.assertRaises(ReviewFailure):
                decode("codex", bad, final, 0)

    def test_correct_envelope_wrong_source_location_rejected(self):
        issue = deepcopy(ISSUE)
        issue["evidence"][0]["quote"] = "not in source"
        with self.assertRaises(ReviewFailure):
            run_pass(
                "claude",
                "/fake/host",
                "chosen-model",
                FILES,
                "local:refund.py",
                executor=lambda *args: envelope("claude", [issue]),
            )

    def test_actual_process_stdin_and_exit_capture(self):
        with TemporaryDirectory() as d:
            out, final, code = execute(
                [
                    sys.executable,
                    "-c",
                    "import sys; print(sys.stdin.read()); sys.exit(3)",
                ],
                "authored stdin",
                d,
                timeout=3,
            )
            self.assertEqual(out.strip(), "authored stdin")
            self.assertEqual(code, 3)
            self.assertIsNone(final)

    def test_actual_process_timeout_and_output_limit(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(ReviewFailure, "review_timeout"):
                execute(
                    [sys.executable, "-c", "import time; time.sleep(10)"],
                    "",
                    d,
                    timeout=0.1,
                )
            with self.assertRaisesRegex(ReviewFailure, "review_output_limit"):
                execute(
                    [
                        sys.executable,
                        "-c",
                        'import sys; sys.stdout.write("x"*1100000); sys.stdout.flush()',
                    ],
                    "",
                    d,
                    timeout=3,
                )

    def test_duplicate_json_key_and_unexpected_fields_rejected(self):
        with self.assertRaises(ReviewFailure):
            decode("claude", '{"type":"result","type":"other"}', None, 0)
        out, _, _ = envelope("claude", [])
        v = json.loads(out)
        v["structured_output"]["success"] = True
        with self.assertRaises(ReviewFailure):
            decode("claude", json.dumps(v), None, 0)


if __name__ == "__main__":
    unittest.main()
