"""Offline Stage 2 checks. No fixture pass certifies a live API call."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from shop_assistant.business import ShopService
from .fixtures import SequenceTransport, SCENARIOS, message, text, call
from .loop import run_loop
from .transport import MessagesTransport, TransportFailure, NoRedirect


class LoopChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.shop = ShopService(Path(self.directory.name))

    def run_case(self, responses, **kwargs):
        send = SequenceTransport(responses)
        result = run_loop(send, self.shop, "Inspect O-1001", **kwargs)
        return result, send

    def test_round_trip_preserves_assistant_and_exact_result_id(self):
        result, send = self.run_case(SCENARIOS["happy"])
        self.assertEqual(result["status"], "ended")
        self.assertEqual(len(send.requests), 2)
        history = send.requests[1]
        self.assertEqual(history[1], {"role": "assistant", "content": SCENARIOS["happy"][0]["content"]})
        self.assertEqual(history[2]["role"], "user")
        block = history[2]["content"][0]
        self.assertEqual(block["type"], "tool_result")
        self.assertEqual(block["tool_use_id"], "u1")
        self.assertEqual(json.loads(block["content"])["id"], "O-1001")
        self.assertEqual(self.shop.ledger(), [])

    def test_multiple_and_subsequent_calls_all_get_results(self):
        result, send = self.run_case(SCENARIOS["multiple"])
        self.assertEqual(result["status"], "ended")
        self.assertEqual([b["tool_use_id"] for b in send.requests[1][-1]["content"]], ["u1", "u2"])
        self.assertEqual(send.requests[2][-1]["content"][0]["tool_use_id"], "u3")
        self.assertEqual(sum(e["kind"] == "call" for e in self.shop.events()), 3)

    def test_missing_order_is_error_result_not_fake_success(self):
        result, send = self.run_case(SCENARIOS["missing"])
        error = send.requests[1][-1]["content"][0]
        self.assertTrue(error["is_error"])
        self.assertEqual(json.loads(error["content"])["error"]["code"], "ORDER_NOT_FOUND")
        self.assertEqual(result["status"], "ended")  # turn ended, support case not resolved
        self.assertEqual(result["tool_errors"], 1)

    def test_text_does_not_override_abnormal_stop_or_execute_truncated_call(self):
        for reason in ["max_tokens", "pause_turn", "refusal", "stop_sequence", "model_context_window_exceeded", "new_reason"]:
            with self.subTest(reason=reason):
                result, send = self.run_case([message(reason, text("All done"), call("u1"))])
                self.assertEqual(result["status"], "interrupted")
                self.assertEqual(result["stop_reason"], reason)
                self.assertEqual(len(send.requests), 1)
                self.assertEqual(self.shop.events(), [])

    def test_end_turn_with_no_text_still_ends_without_retry(self):
        result, send = self.run_case([message("end_turn")])
        self.assertEqual(result["status"], "ended")
        self.assertEqual(result["text"], "")
        self.assertEqual(len(send.requests), 1)

    def test_turn_bound_is_interruption_not_primary_success_signal(self):
        result, send = self.run_case([message("tool_use", call("u1"))], max_turns=1)
        self.assertEqual(result["status"], "interrupted")
        self.assertEqual(result["stop_reason"], "turn_limit")
        self.assertEqual(len(send.requests), 1)
        self.assertEqual(result["history"][-1]["content"][0]["tool_use_id"], "u1")

    def test_unknown_tool_and_bad_arguments_never_dispatch_mutations(self):
        calls = [call("u1", name="record_refund"), call("u2")]
        calls[1]["input"] = {"order_id": "O-1001", "refund": True}
        result, send = self.run_case([message("tool_use", *calls), message("end_turn")])
        self.assertEqual(result["tool_errors"], 2)
        self.assertTrue(all(b["is_error"] for b in send.requests[1][-1]["content"]))
        self.assertEqual(self.shop.events(), [])
        self.assertEqual(self.shop.ledger(), [])

    def test_malformed_and_duplicate_ids_fail_before_any_dispatch(self):
        invalid = [message("tool_use"), message("tool_use", call("same"), call("same")),
                   message("end_turn", call("u1")), {"content": []},
                   message("tool_use", {"type": "tool_use", "id": "u1"}),
                   message("tool_use", {"type": "unknown"})]
        for value in invalid:
            with self.subTest(value=value):
                result, _ = self.run_case([value])
                self.assertEqual(result["status"], "interrupted")
                self.assertEqual(result["stop_reason"], "protocol_error")
                self.assertEqual(self.shop.events(), [])

    def test_reused_id_in_later_turn_is_rejected(self):
        result, _ = self.run_case([message("tool_use", call("u1")), message("tool_use", call("u1"))])
        self.assertEqual(result["stop_reason"], "protocol_error")
        self.assertEqual(sum(e["kind"] == "call" for e in self.shop.events()), 1)

    def test_transport_failure_is_safe_and_keeps_history(self):
        def fail(history):
            raise TransportFailure("http_429")
        result = run_loop(fail, self.shop, "Inspect O-1001")
        self.assertEqual(result["status"], "interrupted")
        self.assertEqual(result["stop_reason"], "transport_error")
        self.assertEqual(result["trace"][-1]["detail"], "http_429")

    def test_input_response_not_mutated_and_history_snapshots_are_stable(self):
        values = copy.deepcopy(SCENARIOS["multiple"])
        original = copy.deepcopy(values)
        result, send = self.run_case(values)
        self.assertEqual(values, original)
        self.assertEqual(len(send.requests[0]), 1)
        self.assertGreater(len(result["history"]), len(send.requests[0]))


class TransportChecks(unittest.TestCase):
    def test_missing_environment_fails_without_network(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(TransportFailure, "missing_local_model_or_key"):
                MessagesTransport.from_environment()

    def test_http_protocol_failures_are_sanitized(self):
        import http.client
        for failure in [http.client.IncompleteRead(b"PRIVATE-BODY"),
                        http.client.BadStatusLine("PRIVATE-PROVIDER-LINE")]:
            with self.subTest(failure=type(failure).__name__):
                client = MessagesTransport("test-model", "not-a-real-key")
                with patch.object(client._opener, "open", side_effect=failure):
                    with self.assertRaisesRegex(TransportFailure, "^http_protocol_failure$"):
                        client([{"role": "user", "content": "fixture"}])

    def test_http_request_contract_is_fixed_and_errors_do_not_expose_key(self):
        import urllib.error
        client = MessagesTransport("test-model", "not-a-real-key")
        captured = []
        def fail(request, timeout):
            captured.append(request)
            self.assertEqual(timeout, 20)
            raise urllib.error.HTTPError(request.full_url, 401, "secret-body", {}, None)
        with patch.object(client._opener, "open", side_effect=fail):
            with self.assertRaisesRegex(TransportFailure, "^http_401$"):
                client([{"role": "user", "content": "fixture"}])
        req = captured[0]
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(req.get_header("Anthropic-version"), "2023-06-01")
        payload = json.loads(req.data)
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["tools"][0]["name"], "get_order")
        self.assertIsNone(NoRedirect().redirect_request(req, None, 302, "", {}, "https://elsewhere.invalid"))


if __name__ == "__main__":
    unittest.main()
