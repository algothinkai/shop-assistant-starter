from copy import deepcopy
import unittest
from .fixtures import FILES, ISSUE, reports
from .workflow import ReviewFailure, plan, aggregate


class ReviewChecks(unittest.TestCase):
    def test_per_file_and_integration_passes_are_required(self):
        p = plan(FILES)
        self.assertEqual(len(p["passes"]), 4)
        self.assertEqual(p["passes"][-1]["files"], sorted(FILES))
        empty = reports()
        for r in empty:
            r["findings"] = []
        self.assertEqual(aggregate(FILES, empty)["status"], "completed")
        self.assertEqual(aggregate(FILES, empty[:-1])["status"], "incomplete")

    def test_same_anchored_cause_deduplicates_but_keeps_evidence(self):
        result = aggregate(FILES, reports())
        self.assertEqual(len(result["issues"]), 1)
        issue = result["issues"][0]
        self.assertEqual(len(issue["observations"]), 2)
        self.assertEqual(len(issue["observations"][-1]["evidence"]), 2)

    def test_failed_pass_retains_partial_findings_and_is_not_clean(self):
        rows = reports()
        rows[-1]["status"] = "failed"
        result = aggregate(FILES, rows)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(len(result["issues"][0]["observations"]), 2)
        self.assertEqual(result["incomplete_passes"], ["integration"])

    def test_wrong_revision_duplicate_or_unknown_pass_rejected(self):
        for mode in ("revision", "duplicate", "unknown"):
            rows = reports()
            if mode == "revision":
                rows[0]["revision"] = "0" * 64
            elif mode == "duplicate":
                rows[1] = deepcopy(rows[0])
            else:
                rows[0]["pass_id"] = "unplanned"
            with self.assertRaises(ReviewFailure):
                aggregate(FILES, rows)

    def test_unbound_location_and_out_of_scope_file_rejected(self):
        for mode in ("line", "quote", "scope"):
            rows = reports()
            item = rows[1]["findings"][0]
            if mode == "line":
                item["evidence"][0]["line"] = True
            elif mode == "quote":
                item["evidence"][0]["quote"] = "invented"
            else:
                item["evidence"].append(
                    {
                        "path": "payment.py",
                        "line": 1,
                        "quote": FILES["payment.py"].splitlines()[0],
                    }
                )
            with self.assertRaises(ReviewFailure):
                aggregate(FILES, rows)

    def test_severity_disagreement_is_preserved_not_voted_away(self):
        rows = reports()
        rows[-1]["findings"][0]["severity"] = "P1"
        result = aggregate(FILES, rows)
        self.assertTrue(result["issues"][0]["severity_disagreement"])
        self.assertEqual(
            {o["severity"] for o in result["issues"][0]["observations"]}, {"P1", "P2"}
        )

    def test_prior_rerun_distinguishes_still_reported_from_absence(self):
        initial = aggregate(FILES, reports())
        prior = {
            "revision": initial["revision"],
            "issues": [
                {
                    k: v
                    for k, v in initial["issues"][0].items()
                    if k in ("fingerprint", "path", "symbol", "cause")
                }
            ],
        }
        self.assertEqual(
            aggregate(FILES, reports(), prior)["issues"][0]["rerun_status"],
            "still_reported",
        )
        empty = reports()
        for r in empty:
            r["findings"] = []
        result = aggregate(FILES, empty, prior)
        self.assertEqual(len(result["not_reobserved"]), 1)
        self.assertIn("not proven fixed", result["limitation"])

    def test_confidence_does_not_override_validation(self):
        rows = reports()
        rows[1]["findings"][0]["confidence"] = True
        with self.assertRaises(ReviewFailure):
            aggregate(FILES, rows)
        rows = reports()
        rows[1]["findings"][0]["confidence"] = 0.1
        self.assertEqual(len(aggregate(FILES, rows)["issues"]), 1)

    def test_distinct_causes_at_same_symbol_remain_separate(self):
        rows = reports()
        other = deepcopy(ISSUE)
        other["cause"] = "missing_identity_guard"
        rows[1]["findings"].append(other)
        self.assertEqual(len(aggregate(FILES, rows)["issues"]), 2)

    def test_inputs_are_unchanged(self):
        rows = reports()
        before = deepcopy(rows)
        aggregate(FILES, rows)
        self.assertEqual(rows, before)


if __name__ == "__main__":
    unittest.main()
