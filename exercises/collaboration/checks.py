"""Intentional Stage 1 acceptance checks; excluded from baseline discovery."""
import copy
import tempfile
import unittest
from pathlib import Path

from shop_assistant.business import ShopService
from .report import summarize_run
from .service import case_report


class RunReportChecks(unittest.TestCase):
    def test_real_runs_do_not_contaminate_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            shop = ShopService(Path(directory))
            good = shop.run_preset("T-1001")
            bad = shop.run_preset("T-1004")
            self.assertEqual(case_report(shop, good["run_id"]), {
                "run_id": good["run_id"], "calls": 2, "errors": 0, "status": "completed"})
            self.assertEqual(case_report(shop, bad["run_id"]), {
                "run_id": bad["run_id"], "calls": 1, "errors": 1, "status": "blocked"})
            self.assertEqual(shop.ledger(), [])

    def test_successful_tool_without_outcome_is_incomplete(self):
        events = [{"run_id": "A", "kind": "call"}, {"run_id": "A", "kind": "result"}]
        self.assertEqual(summarize_run(events, "A"), {
            "run_id": "A", "calls": 1, "errors": 0, "status": "incomplete"})

    def test_missing_run_is_incomplete(self):
        self.assertEqual(summarize_run([], "missing"), {
            "run_id": "missing", "calls": 0, "errors": 0, "status": "incomplete"})

    def test_human_review_is_not_completed(self):
        with tempfile.TemporaryDirectory() as directory:
            shop = ShopService(Path(directory))
            result = shop.run_preset("T-1002")
            self.assertEqual(case_report(shop, result["run_id"])["status"], "needs_human_review")

    def test_repeat_same_ticket_keeps_runs_separate_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            shop = ShopService(Path(directory))
            first = shop.run_preset("T-1001")
            shop.run_preset("T-1001")
            events = shop.events()
            saved = copy.deepcopy(events)
            self.assertEqual(summarize_run(events, first["run_id"])["calls"], 2)
            self.assertEqual(events, saved)


if __name__ == "__main__":
    unittest.main()
