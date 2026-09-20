"""Observable measurement and failure-boundary checks."""
from copy import deepcopy
import unittest
from .fixtures import CASES, authored
from .workflow import QualityError, dataset, measure, route


class QualityChecks(unittest.TestCase):
    def test_counts_rates_and_high_confidence_false_positive(self):
        result = measure(CASES, authored())
        self.assertEqual({k: result["overall"][k] for k in ("tp", "fp", "fn", "tn")}, dict(tp=2, fp=1, fn=1, tn=2))
        self.assertAlmostEqual(result["overall"]["precision"], 2/3)
        self.assertAlmostEqual(result["overall"]["false_positive_rate_on_resolved"], 1/3)
        self.assertEqual(result["confidence_bands"]["at_least_0.8"]["observed_precision"], .5)
        self.assertEqual(result["confidence_bands"]["below_0.8"]["observed_precision"], 1)

    def test_category_pause_retains_real_issue_and_never_auto_accepts(self):
        output = route(CASES, authored(revised=True), ["comments"])
        destinations = {r["id"]: r["destination"] for r in output["routes"]}
        self.assertEqual(destinations["d4"], "held_for_prompt_revision")
        self.assertEqual(destinations["d1"], "human_review")
        self.assertFalse(output["auto_accepted"])
        self.assertEqual(output["measurement"]["overall"]["tp"], 3)

    def test_missing_failed_are_unresolved_not_negatives(self):
        run = authored()
        run["judgments"].pop()
        run["judgments"][0].update(verdict="failed", confidence=None)
        result = measure(CASES, run)
        self.assertFalse(result["complete"])
        self.assertEqual(result["overall"]["unresolved"], 2)
        self.assertEqual(result["overall"]["tn"], 2)
        self.assertEqual(route(CASES, run, [])["routes"][0]["destination"], "rerun_or_investigate")

    def test_empty_denominators_not_perfect_score(self):
        run = authored(); run["judgments"] = []
        result = measure(CASES, run)
        self.assertIsNone(result["overall"]["precision"])
        self.assertIsNone(result["overall"]["recall_on_resolved"])
        self.assertIsNone(result["overall"]["false_positive_rate_on_resolved"])

    def test_wrong_split_duplicate_unknown_rejected(self):
        for changed in ("h1", "d2", "unknown"):
            run = authored(); run["judgments"][0]["id"] = changed
            with self.assertRaises(QualityError): measure(CASES, run)
        self.assertTrue(measure(CASES, authored("held_out"))["complete"])

    def test_every_source_label_and_criteria_binding(self):
        for field, value in (("source", "changed"), ("is_issue", False), ("rationale", "changed")):
            cases = deepcopy(CASES); cases[0][field] = value
            with self.assertRaises(QualityError): measure(cases, authored())
        self.assertEqual(dataset(CASES), dataset(list(reversed(CASES))))
        run = authored(); run["criteria_version"] = ""
        with self.assertRaises(QualityError): measure(CASES, run)

    def test_confidence_validation_no_coercion(self):
        for value in (True, "0.9", float("nan"), float("inf"), -.1, 1.1):
            run = authored(); run["judgments"][0]["confidence"] = value
            with self.assertRaises(QualityError): measure(CASES, run)
        run = authored(); run["judgments"][1]["confidence"] = .5
        with self.assertRaises(QualityError): measure(CASES, run)

    def test_paused_categories_explicit_unique_known(self):
        for value in (["unknown"], ["comments", "comments"], [True], "comments"):
            with self.assertRaises(QualityError): route(CASES, authored(), value)

    def test_authored_provenance_survives_perfect_revised_fixture(self):
        result = measure(CASES, authored("held_out", revised=True))
        self.assertEqual(result["overall"]["precision"], 1)
        self.assertEqual(result["provenance"], "authored")
        self.assertIn("NOT_OPEN_ENDED", result["scope"])

    def test_malformed_cases_and_reports_rejected(self):
        for cases in ([], CASES + [CASES[0]], [dict(CASES[0], is_issue=1)]):
            with self.assertRaises(QualityError): dataset(cases)
        for update in ({"provenance": "verified_live"}, {"judgments": {}}, {"extra": 1}):
            run = authored(); run.update(update)
            with self.assertRaises(QualityError): measure(CASES, run)
