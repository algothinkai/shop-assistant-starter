"""Offline ordering, schema and failure contracts; no model calls."""
from copy import deepcopy
import json
import unittest
from unittest.mock import Mock
from ..extraction.fixtures import SOURCE, CANDIDATE
from ..extraction_reconciliation.fixtures import SCENARIOS
from ..extraction_reconciliation.reconciliation import reconcile
from .workflow import build_request, run


def response(name="extract_receipt", candidate=None):
    return {"type": "message", "role": "assistant", "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "fixture", "name": name,
                         "input": deepcopy(CANDIDATE if candidate is None else candidate)}]}


def request():
    return {"source": SOURCE, "failed_candidate": None, "validation_errors": []}


class OrchestrationChecks(unittest.TestCase):
    def test_unknown_any_and_known_forced(self):
        unknown = build_request("test", request())
        self.assertEqual(unknown["tool_choice"], {"type": "any", "disable_parallel_tool_use": True})
        self.assertEqual({t["name"] for t in unknown["tools"]}, {"extract_receipt", "reconcile_receipt"})
        self.assertTrue(all(t["strict"] for t in unknown["tools"]))
        for name in ("extract_receipt", "reconcile_receipt"):
            known = build_request("test", request(), kind=name)
            self.assertEqual(known["tool_choice"]["name"], name)
            self.assertEqual([t["name"] for t in known["tools"]], [name])

    def test_forced_extraction_and_validation_precede_real_enrichment(self):
        seen = []
        def send(payload):
            seen.append("extract")
            self.assertNotIn("get_order", [t["name"] for t in payload["tools"]])
            return response()
        def enrich(oid):
            seen.append("enrich")
            return {"id": oid}
        r = run(SOURCE, "test", send, mode="authored_fixture_no_model", kind="extract_receipt", enrich=enrich)
        self.assertEqual(seen, ["extract", "enrich"])
        self.assertEqual(r["status"], "enriched")
        phases = [e["phase"] for e in r["trace"]]
        self.assertLess(phases.index("validation"), phases.index("enrichment"))

    def test_reconciliation_selected_and_checked_without_order_lookup(self):
        source = SCENARIOS["consistent"];enrich = Mock()
        r = run(source, "test", Mock(return_value=response("reconcile_receipt", reconcile(source)["record"])), mode="authored_fixture_no_model", enrich=enrich)
        self.assertEqual(r["status"], "validated_candidate")
        self.assertEqual(r["schema"], "reconcile_receipt")
        enrich.assert_not_called()

    def test_source_conflict_stops_after_one_request_and_no_enrichment(self):
        source = SCENARIOS["mismatch"];send = Mock(return_value=response("reconcile_receipt", reconcile(source)["record"]));enrich = Mock()
        r = run(source, "test", send, mode="authored_fixture_no_model", enrich=enrich)
        self.assertEqual(r["status"], "needs_human_review")
        self.assertEqual(send.call_count, 1);enrich.assert_not_called()

    def test_wrong_reconciliation_candidate_gets_source_and_error_retry(self):
        source = SCENARIOS["consistent"];good = reconcile(source)["record"];bad = deepcopy(good);bad["calculated_total_cents"] = 1
        send = Mock(side_effect=[response("reconcile_receipt", bad), response("reconcile_receipt", good)])
        r = run(source, "test", send, mode="authored_fixture_no_model")
        self.assertEqual(r["status"], "validated_candidate")
        retry = send.call_args_list[1].args[0]
        self.assertEqual(retry["tool_choice"]["name"], "reconcile_receipt")
        user = json.loads(retry["messages"][0]["content"])
        self.assertEqual(user["source"], source)
        self.assertEqual(user["failed_candidate"], bad)
        self.assertIn("calculated_total_cents", user["validation_errors"])

    def test_exhaustion_and_missing_facts_never_enrich(self):
        bad = deepcopy(CANDIDATE);bad["total_cents"]["value"] = 1
        send = Mock(return_value=response(candidate=bad));enrich = Mock()
        r = run(SOURCE, "test", send, mode="authored_fixture_no_model", enrich=enrich)
        self.assertEqual(r["status"], "validation_failed");self.assertEqual(send.call_count, 2);enrich.assert_not_called()
        missing = deepcopy(CANDIDATE);missing["customer_name"] = {"value": None, "evidence": None}
        source = SOURCE.replace("Customer: Noor Patel\n", "")
        r = run(source, "test", Mock(return_value=response(candidate=missing)), mode="authored_fixture_no_model", enrich=enrich)
        self.assertEqual(r["status"], "needs_human_review");enrich.assert_not_called()

    def test_schema_switch_or_wrong_tool_cannot_bypass_retry(self):
        bad = deepcopy(CANDIDATE);bad["total_cents"]["value"] = 1
        send = Mock(side_effect=[response(candidate=bad), response("reconcile_receipt", {})]);enrich = Mock()
        r = run(SOURCE, "test", send, mode="authored_fixture_no_model", enrich=enrich)
        self.assertEqual(r["status"], "generation_failed");enrich.assert_not_called()
        for name in ("get_order", "record_refund", "reconcile_receipt"):
            r = run(SOURCE, "test", Mock(return_value=response(name)), mode="authored_fixture_no_model", kind="extract_receipt", enrich=enrich)
            self.assertEqual(r["status"], "generation_failed")

    def test_enrichment_failure_or_wrong_order_is_not_success(self):
        for callback in [Mock(side_effect=RuntimeError("PRIVATE")), Mock(return_value={"id": "O-9999"}), Mock(return_value={"error": "PRIVATE"})]:
            r = run(SOURCE, "test", Mock(return_value=response()), mode="authored_fixture_no_model", enrich=callback)
            self.assertEqual(r["status"], "enrichment_failed")
            self.assertNotIn("PRIVATE", json.dumps(r))

    def test_abnormal_terminal_and_transport_failure_do_not_retry(self):
        abnormal = response();abnormal["stop_reason"] = "max_tokens"
        for send in [Mock(return_value=abnormal), Mock(side_effect=RuntimeError("SECRET"))]:
            enrich = Mock();r = run(SOURCE, "test", send, mode="live_model", enrich=enrich)
            self.assertEqual(r["status"], "generation_failed");self.assertEqual(send.call_count, 1);enrich.assert_not_called()
            self.assertNotIn("SECRET", json.dumps(r))

    def test_invalid_mode_or_kind_rejected_before_dispatch(self):
        for kwargs in [dict(mode="fake_live"), dict(mode="live_model", kind="record_refund")]:
            send = Mock()
            with self.assertRaises(ValueError):
                run(SOURCE, "test", send, **kwargs)
            send.assert_not_called()

    def test_compact_schema_cannot_skip_arithmetic_source_conflict(self):
        source = SCENARIOS["mismatch"] + "Order: O-1003\nDate: 2026-08-28\nCustomer: Noor Patel\n"
        candidate = deepcopy(CANDIDATE)
        candidate["total_cents"] = {"value": 5530, "evidence": "Total: USD 55.30"}
        candidate["currency"]["evidence"] = "Total: USD 55.30"
        enrich = Mock(return_value={"id": "O-1003"})
        r = run(source, "test", Mock(return_value=response(candidate=candidate)), mode="authored_fixture_no_model", enrich=enrich)
        self.assertEqual(r["status"], "needs_human_review")
        enrich.assert_not_called()

    def test_unrecognized_or_malformed_charge_lines_cannot_enrich(self):
        for line in ("Handling: USD 1.00", "Tax : USD 3.80", "Mystery surcharge 1.00", "Item: shipping USD 1.00 x1"):
            enrich = Mock(return_value={"id": "O-1003"})
            r = run(SOURCE + line + "\n", "test", Mock(return_value=response()), mode="authored_fixture_no_model", enrich=enrich)
            self.assertEqual(r["status"], "needs_human_review", line)
            enrich.assert_not_called()

    def test_each_schema_has_scoped_instructions(self):
        payload = build_request("test", request())
        self.assertIn("<compact_receipt_only>", payload["system"])
        self.assertIn("</compact_receipt_only>", payload["system"])
        self.assertIn("no evidence fields", payload["system"])
