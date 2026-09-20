"""Protocol/transport failure tests are offline, never live evidence."""
from copy import deepcopy
import io
import json
import unittest
from unittest.mock import Mock, patch
import urllib.error
from ..extraction.fixtures import CANDIDATE, SOURCE
from ..extraction.pipeline import extract
from .adapter import ExtractionFailure, Generator, build_request, read_candidate
from .demo import authored_response, main
from .transport import Transport


def request():
    return {"source": SOURCE, "failed_candidate": None, "validation_errors": []}


class MessagesExtractionChecks(unittest.TestCase):
    def test_strict_forced_schema_and_bounded_request(self):
        payload = build_request("local-test-model", request())
        self.assertEqual(payload["max_tokens"], 2048)
        self.assertEqual(payload["tool_choice"], {"type": "tool", "name": "extract_receipt", "disable_parallel_tool_use": True})
        self.assertTrue(payload["tools"][0]["strict"])
        self.assertEqual(payload["tools"][0]["name"], "extract_receipt")
        self.assertNotIn("thinking", payload)
        self.assertEqual(json.loads(payload["messages"][0]["content"]), request())
        self.assertFalse(payload["tools"][0]["input_schema"]["additionalProperties"])

    def test_reads_one_named_tool_only_and_returns_copy(self):
        response = authored_response(None)
        candidate = read_candidate(response)
        self.assertEqual(candidate, CANDIDATE)
        candidate["currency"]["value"] = "XXX"
        self.assertEqual(response["content"][0]["input"], CANDIDATE)

    def test_abnormal_stop_and_text_only_never_success(self):
        for reason in ["end_turn", "max_tokens", "pause_turn", "refusal", None]:
            response = authored_response(None); response["stop_reason"] = reason
            with self.subTest(reason=reason), self.assertRaises(ExtractionFailure):
                read_candidate(response)
        response = authored_response(None)
        response["content"] = [{"type": "text", "text": "done"}]
        with self.assertRaises(ExtractionFailure):
            read_candidate(response)

    def test_duplicate_wrong_or_malformed_tool_is_rejected(self):
        for change in [lambda r: r["content"].append(deepcopy(r["content"][0])),
                       lambda r: r["content"][0].update(name="record_refund"),
                       lambda r: r["content"][0].update(input="not an object"),
                       lambda r: r["content"][0].update(id=""),
                       lambda r: r.update(role="user"),
                       lambda r: r["content"].append({"type": "server_tool_use"})]:
            r = authored_response(None); change(r)
            with self.assertRaises(ExtractionFailure):
                read_candidate(r)

    def test_semantic_correction_reuses_pipeline_and_full_feedback(self):
        wrong = authored_response(None); wrong["content"][0]["input"]["total_cents"]["value"] = 1
        send = Mock(side_effect=[wrong, authored_response(None)])
        result = extract(SOURCE, Generator("test-model", send), mode="authored_fixture_no_model")
        self.assertEqual(result["status"], "validated_candidate")
        self.assertEqual(send.call_count, 2)
        correction = json.loads(send.call_args_list[1].args[0]["messages"][0]["content"])
        self.assertEqual(correction["source"], SOURCE)
        self.assertEqual(correction["failed_candidate"]["total_cents"]["value"], 1)
        self.assertTrue(correction["validation_errors"])

    def test_protocol_failure_stops_without_retry_or_echo(self):
        send = Mock(side_effect=RuntimeError("PRIVATE-KEY-DIAGNOSTIC"))
        result = extract(SOURCE, Generator("test-model", send), mode="live_model")
        self.assertEqual(result["status"], "generation_failed")
        self.assertEqual(send.call_count, 1)
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_request_validation_prevents_dispatch_and_input_mutation(self):
        for model, r in [("", request()), ("bad\nmodel", request()),
                         ("test", {**request(), "source": "x" * 50001}),
                         ("test", {**request(), "extra": True})]:
            send = Mock()
            with self.assertRaises(ExtractionFailure):
                Generator(model, send)(r)
            send.assert_not_called()
        r = request(); before = deepcopy(r)
        payload = build_request("test", r)
        payload["tools"][0]["input_schema"]["required"].clear()
        self.assertEqual(r, before)
        self.assertEqual(len(build_request("test", r)["tools"][0]["input_schema"]["required"]), 5)

    def test_transport_fixed_endpoint_headers_and_size(self):
        t = Transport("LOCAL-FAKE-SECRET")
        response = Mock(); response.read.return_value = json.dumps(authored_response(None)).encode()
        response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
        t._opener = Mock(); t._opener.open.return_value = response
        self.assertEqual(t(build_request("test", request()))["stop_reason"], "tool_use")
        req = t._opener.open.call_args.args[0]
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(req.get_header("Anthropic-version"), "2023-06-01")
        self.assertEqual(t._opener.open.call_args.kwargs["timeout"], 20)
        response.read.assert_called_once_with(100001)
        with self.assertRaises(ExtractionFailure):
            t({"x": "x" * 60001})

    def test_transport_http_and_bad_json_are_safe(self):
        for error in [urllib.error.HTTPError("https://api.anthropic.com", 429, "PRIVATE", {}, io.BytesIO(b"PRIVATE")),
                      TimeoutError("PRIVATE")]:
            t = Transport("LOCAL-FAKE-SECRET"); t._opener = Mock(); t._opener.open.side_effect = error
            with self.assertRaises(ExtractionFailure) as caught:
                t({})
            self.assertNotIn("PRIVATE", str(caught.exception))
        for raw in [b"not-json", b"NaN", b"x" * 100001]:
            t = Transport("LOCAL-FAKE-SECRET"); t._opener = Mock()
            response = Mock(); response.read.return_value = raw
            response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
            t._opener.open.return_value = response
            with self.assertRaises(ExtractionFailure):
                t({})

    def test_default_demo_never_constructs_live_transport(self):
        with patch("sys.argv", ["demo"]), patch("sys.stdout", new_callable=io.StringIO) as output, patch.object(Transport, "from_environment") as transport:
            self.assertEqual(main(), 0)
        transport.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["verification"], "OFFLINE_ONLY")

    def test_missing_live_config_reports_unverified(self):
        with patch("sys.argv", ["demo", "--live"]), patch.dict("os.environ", {}, clear=True), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(main(), 1)
        self.assertEqual(json.loads(output.getvalue())["verification"], "UNVERIFIED")

    def test_live_transport_failure_cannot_claim_success_or_print_response(self):
        with patch("sys.argv", ["demo", "--live"]), patch.dict("os.environ", {"ANTHROPIC_MODEL": "test"}), patch("sys.stdout", new_callable=io.StringIO) as output, patch.object(Transport, "from_environment", return_value=Mock(side_effect=ExtractionFailure("PRIVATE-KEY"))):
            self.assertEqual(main(), 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result["verification"], "UNVERIFIED")
        self.assertEqual(result["generation_calls"], 1)
        self.assertEqual(result["candidates_checked"], 0)
        self.assertNotIn("PRIVATE", output.getvalue())

    def test_redirect_handler_refuses_forwarding(self):
        from ..tool_loop.transport import NoRedirect
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://elsewhere.invalid"))
