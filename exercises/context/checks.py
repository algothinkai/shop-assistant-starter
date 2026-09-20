"""Behavioral stage checks; intentionally separate from foundation tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from .state import new_case, save_snapshot, read_snapshot
from .workflow import record_fact, trim_order, build_context, recover

STAMP = "2026-09-20T12:00:00+00:00"


def fact(state=None, issue="return", value=7600):
    return record_fact(state or new_case("case-1003"), issue, "amount_cents", value, "receipt:R-1003", STAMP)


class ContextChecks(unittest.TestCase):
    def test_issues_do_not_overwrite_each_other(self):
        first = fact()
        second = fact(first, "shipping", 500)
        self.assertEqual(first["issues"]["return"]["amount_cents"][0]["value"], 7600)
        self.assertNotIn("shipping", first["issues"])
        self.assertEqual(second["issues"]["shipping"]["amount_cents"][0]["value"], 500)

    def test_conflicts_preserve_source_observations(self):
        state = fact(fact(), value=7500)
        state = fact(state, value=7500)
        self.assertEqual(len(state["issues"]["return"]["amount_cents"]), 2)
        result = build_context(state, [{"role":"user", "content":"Please check."}], "A small charge")
        self.assertEqual(result["conflicts"], [{"issue":"return", "field":"amount_cents"}])
        self.assertEqual(result["status"], "needs_review")
        self.assertIn("7600", result["system"])
        self.assertIn("7500", result["system"])
        self.assertIn("receipt:R-1003", result["system"])

    def test_exact_date_expectation_and_amount_outside_summary(self):
        state = fact()
        for field,value in [("delivered_on","2026-09-01"),("customer_expectation","Replacement by 2026-09-25, not a refund")]:
            state = record_fact(state,"return",field,value,"customer:turn-1",STAMP)
        context = build_context(state, [{"role":"user","content":"Keep the date."}], "Customer wants help")
        self.assertTrue(context["system"].startswith("CASE FACTS"))
        for fragment in ["7600","2026-09-01","2026-09-25","not a refund",STAMP]:
            self.assertIn(fragment, context["system"])
        self.assertLess(context["system"].index("2026-09-25"), context["system"].index("NARRATIVE SUMMARY"))

    def test_preserves_full_history_and_tool_pairing_without_aliases(self):
        history = [{"role":"user","content":"Find order"},{"role":"assistant","content":[{"type":"tool_use","id":"lookup-1","name":"get_order","input":{"order_id":"O-1003"}}]}, {"role":"user","content":[{"type":"tool_result","tool_use_id":"lookup-1","content":"order found"}]}]
        original=copy.deepcopy(history)
        result=build_context(fact(), history, "Summary")
        self.assertEqual(result["messages"],original)
        result["messages"][1]["content"][0]["id"]="changed"
        self.assertEqual(history,original)

    def test_order_projection_retains_meaning_and_removes_verbose_fields(self):
        result={"id":"O-1003","status":"delivered","total_cents":7600,"delivered_on":"2026-09-01","shipping":"Delivered","marketing":"x"*10000,"internal_notes":"irrelevant"}
        trimmed=trim_order(result)
        self.assertEqual(set(trimmed),{"id","status","total_cents","delivered_on","shipping"})
        self.assertEqual(trimmed["total_cents"],7600)
        self.assertIn("marketing",result)

    def test_projection_preserves_error_and_missing_data(self):
        error={"error":{"code":"MISSING_ORDER","retryable":False,"message":"Not found"}}
        self.assertEqual(trim_order(error),error)
        with self.assertRaises(ValueError): trim_order({"status":"delivered"})
        self.assertIsNone(trim_order({"id":"O-1003","delivered_on":None})["delivered_on"])

    def test_round_trip_resumes_matching_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"case.json"; state=fact();save_snapshot(path,state,{"policy":"v1","orders":"v2"})
            result=recover(path,{"policy":"v1","orders":"v2"})
            self.assertEqual(result["status"],"ready")
            self.assertEqual(result["case"],state)
            self.assertEqual(result["changed_sources"],[])

    def test_changed_removed_and_added_sources_require_refresh(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"case.json";save_snapshot(path,fact(),{"policy":"v1","orders":"v2"})
            for current in [{"policy":"v2","orders":"v2"},{"policy":"v1"},{"policy":"v1","orders":"v2","new":"v1"}]:
                result=recover(path,current)
                self.assertEqual(result["status"],"refresh_required")
                self.assertIsNone(result["case"])
                self.assertEqual(result["prior_case"]["case_id"],"case-1003")
                self.assertTrue(result["changed_sources"])

    def test_corruption_does_not_become_empty_success(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"case.json";path.write_text("{broken")
            with self.assertRaises(ValueError):recover(path,{"policy":"v1"})
            self.assertEqual(path.read_text(),"{broken")

    def test_invalid_update_cannot_mutate_prior_facts(self):
        state=fact();original=copy.deepcopy(state)
        for field,value in [("amount_cents",True),("amount_cents",1.5),("unexpected","x")]:
            with self.assertRaises(ValueError):record_fact(state,"return",field,value,"receipt",STAMP)
        self.assertEqual(state,original)

    def test_full_context_bound_fails_without_silent_truncation(self):
        history=[{"role":"user","content":"x"*200001}]
        with self.assertRaises(ValueError):build_context(fact(),history,"Summary")
        self.assertEqual(len(history[0]["content"]),200001)
