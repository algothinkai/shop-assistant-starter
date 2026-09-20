"""Observable evaluation risks, with no vendor calls."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from .evaluation import evaluate


def data():
    rows = json.loads(Path(__file__).with_name("labeled.json").read_text())["rows"]
    return ([r for r in rows if r["split"] == "calibration"],
            [r for r in rows if r["split"] == "evaluation"])


class EvaluationChecks(unittest.TestCase):
    def test_segments_reveal_masked_errors(self):
        c, e = data()
        report = evaluate(c, e)
        self.assertEqual(report["overall"], {"correct": 17, "count": 20, "accuracy": .85})
        segment = report["segments"]["inline"]["total_cents"]
        self.assertEqual(segment, {"correct": 0, "count": 2, "accuracy": 0.0})
        self.assertEqual(report["segments"]["labeled"]["total_cents"]["accuracy"], 1)

    def test_calibration_uses_only_training_labels(self):
        c, e = data()
        first = evaluate(c, e)
        changed = deepcopy(e)
        for row in changed:
            row["gold"] = deepcopy(row["predicted"])
        second = evaluate(c, changed)
        self.assertEqual(first["thresholds"], second["thresholds"])
        self.assertEqual(first["routing"], second["routing"])
        self.assertEqual(first["thresholds"]["labeled"]["total_cents"], .82)
        self.assertIsNone(first["thresholds"]["inline"]["total_cents"])

    def test_overlap_duplicate_wrong_split_fail(self):
        c, e = data()
        with self.assertRaises(ValueError):
            evaluate(c, c)
        e[0]["id"] = c[0]["id"]
        with self.assertRaises(ValueError):
            evaluate(c, e)
        c, e = data()
        with self.assertRaises(ValueError):
            evaluate(c + [c[0]], e)

    def test_unseen_segment_and_insufficient_support_need_review(self):
        c, e = data()
        e[0]["document_type"] = "handwritten"
        report = evaluate(c, e)
        self.assertIn("uncalibrated:total_cents", report["routing"][0]["reasons"])
        report = evaluate(c, e, min_support=3)
        self.assertTrue(all(r["decision"] == "human_review" for r in report["routing"]))

    def test_missing_ambiguity_conflict_override_high_scores(self):
        c, e = data()
        e[0]["source_issue"] = "contradictory"
        e[1]["source_issue"] = "ambiguous"
        e[1]["predicted"]["customer_name"] = None
        report = evaluate(c, e)
        self.assertIn("source:contradictory", report["routing"][0]["reasons"])
        self.assertIn("source:ambiguous", report["routing"][1]["reasons"])
        self.assertIn("missing:customer_name", report["routing"][1]["reasons"])
        self.assertEqual(report["review_queue"][0], "E-1")
        self.assertEqual(report["review_queue"][1], "E-2")

    def test_low_score_routes_review(self):
        c, e = data()
        e[0]["confidence"]["currency"] = .2
        self.assertIn("low_confidence:currency", evaluate(c, e)["routing"][0]["reasons"])

    def test_stratified_sample_includes_high_confidence_and_is_reproducible(self):
        c, e = data()
        r = evaluate(c, e)
        samples = r["audit_sample"]
        self.assertEqual(len(samples), 3)
        self.assertEqual({(s["document_type"], s["confidence_band"]) for s in samples},
                         {("labeled", "high"), ("labeled", "other"), ("inline", "high")})
        self.assertEqual(samples, evaluate(c, list(reversed(e)))["audit_sample"])
        self.assertEqual(len({s["id"] for s in samples}), 3)

    def test_confidence_bins_compare_scores_to_observed_labels(self):
        c, e = data()
        r = evaluate(c, e)
        high = r["confidence_bins"]["inline"]["total_cents"]["high"]
        self.assertEqual(high["count"], 2)
        self.assertEqual(high["accuracy"], 0)
        self.assertAlmostEqual(high["mean_confidence"], .955)

    def test_reject_invalid_confidence_types_values_and_gold(self):
        for bad in [True, float("nan"), float("inf"), -.1, 1.1, "0.9"]:
            c, e = data()
            e[0]["confidence"]["currency"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                evaluate(c, e)
        c, e = data()
        e[0]["predicted"]["total_cents"] = True
        with self.assertRaises(ValueError):
            evaluate(c, e)
        c, e = data()
        del e[0]["gold"]["currency"]
        with self.assertRaises(ValueError):
            evaluate(c, e)

    def test_invalid_parameters_and_empty_sets_fail(self):
        c, e = data()
        for args in [dict(min_support=0), dict(min_support=True),
                     dict(sample_per_stratum=0), dict(target_accuracy=float("nan")),
                     dict(target_accuracy=1.1), dict(seed=True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                evaluate(c, e, **args)
        with self.assertRaises(ValueError):
            evaluate([], e)
        with self.assertRaises(ValueError):
            evaluate(c, [])

    def test_null_gold_counts_accuracy_but_cannot_automate(self):
        c, e = data()
        e[0]["gold"]["customer_name"] = None
        e[0]["predicted"]["customer_name"] = None
        report = evaluate(c, e)
        self.assertIn("missing:customer_name", report["routing"][0]["reasons"])
        self.assertEqual(report["segments"]["labeled"]["customer_name"]["accuracy"], 1)

    def test_inputs_not_mutated_or_echoed_in_report(self):
        c, e = data()
        before = deepcopy((c, e))
        report = evaluate(c, e)
        self.assertEqual((c, e), before)
        self.assertNotIn("Ari Finch", json.dumps(report))
        self.assertNotIn("Order:", json.dumps(report))
