"""Observable arithmetic/provenance/category risks; no service calls."""
from copy import deepcopy
import unittest
from .fixtures import SOURCE, SCENARIOS
from .reconciliation import reconcile, validate_candidate


class ReconciliationChecks(unittest.TestCase):
    def test_consistent_stated_and_computed_values_are_distinct(self):
        report = reconcile(SOURCE)
        self.assertEqual(report["status"], "reconciled")
        self.assertEqual(report["record"], {"stated_total_cents": 5430, "calculated_total_cents": 5430,
                                          "difference_cents": 0, "conflict_detected": False,
                                          "category": "filter", "category_detail": None})
        self.assertEqual(report["item_subtotal_cents"], 4750)
        self.assertIn("Total: USD 54.30", [o["source"] for o in report["observations"]])

    def test_mismatch_preserves_both_totals_instead_of_rewriting(self):
        report = reconcile(SCENARIOS["mismatch"])
        self.assertEqual(report["status"], "needs_human_review")
        self.assertEqual(report["record"]["stated_total_cents"], 5530)
        self.assertEqual(report["record"]["calculated_total_cents"], 5430)
        self.assertEqual(report["record"]["difference_cents"], -100)
        self.assertTrue(report["record"]["conflict_detected"])
        self.assertIn("total_mismatch", report["issues"])

    def test_stated_subtotal_cannot_override_item_sum(self):
        report = reconcile(SOURCE.replace("Subtotal: USD 47.50", "Subtotal: USD 48.50"))
        self.assertIn("subtotal_mismatch", report["issues"])
        self.assertEqual(report["record"]["calculated_total_cents"], 5430)

    def test_missing_charge_is_not_silently_zero(self):
        for name in ("Tax", "Shipping", "Discount", "Subtotal"):
            source = "\n".join(line for line in SOURCE.splitlines() if not line.startswith(name + ":"))
            report = reconcile(source)
            self.assertEqual(report["status"], "needs_human_review")
            self.assertIsNone(report["record"]["calculated_total_cents"])
            self.assertEqual(report["record"]["stated_total_cents"], 5430)

    def test_mixed_currency_and_duplicate_amounts_need_review(self):
        for source in (SCENARIOS["mixed-currency"], SOURCE + "Tax: USD 4.00\n", SOURCE + "Tax: USD 3.80\n"):
            report = reconcile(source)
            self.assertEqual(report["status"], "needs_human_review")
            self.assertIsNone(report["record"]["calculated_total_cents"])
        report = reconcile(SOURCE + "Total: USD 55.00\n")
        self.assertTrue(report["record"]["conflict_detected"])
        self.assertIsNone(report["record"]["stated_total_cents"])
        self.assertEqual(report["record"]["calculated_total_cents"], 5430)

    def test_decimal_cents_avoid_float_and_rounding_guesses(self):
        source = SOURCE.replace("19.75", "0.10").replace("8.00", "0.20").replace("47.50", "0.40").replace("3.80", "0.00").replace("5.00", "0.00").replace("2.00", "0.00").replace("54.30", "0.40")
        self.assertEqual(reconcile(source)["record"]["calculated_total_cents"], 40)
        self.assertEqual(reconcile(source)["issues"], [])
        self.assertIsNone(reconcile(source.replace("USD 0.10", "USD 0.101"))["record"]["calculated_total_cents"])

    def test_bad_quantity_negative_charge_and_unknown_line_are_unresolved(self):
        for source in (SOURCE.replace("x2 @", "x0 @"), SOURCE.replace("USD 3.80", "USD -3.80"), SOURCE + "Handling: USD 1.00\n"):
            report = reconcile(source)
            self.assertEqual(report["status"], "needs_human_review")
            self.assertIsNone(report["record"]["calculated_total_cents"])

    def test_extensible_other_retains_original_detail(self):
        record = reconcile(SCENARIOS["other"])["record"]
        self.assertEqual(record["category"], "other")
        self.assertEqual(record["category_detail"], "repair kit")
        self.assertEqual(reconcile(SOURCE.replace("Category: filter", "Category: FILTER"))["record"]["category"], "filter")

    def test_unclear_missing_and_conflicting_categories_require_review(self):
        for source in (SCENARIOS["unclear"], SOURCE.replace("Category: filter\n", ""), SOURCE + "Category: kettle\n"):
            report = reconcile(source)
            self.assertEqual(report["record"]["category"], "unclear")
            self.assertIsNone(report["record"]["category_detail"])
            self.assertEqual(report["status"], "needs_human_review")

    def test_schema_valid_wrong_proposal_requires_correction(self):
        candidate = reconcile(SOURCE)["record"]; before = deepcopy(candidate)
        self.assertEqual(validate_candidate(SOURCE, candidate)["status"], "validated_candidate")
        candidate["calculated_total_cents"] = 5431
        result = validate_candidate(SOURCE, candidate)
        self.assertEqual(result["status"], "candidate_errors")
        self.assertIn("calculated_total_cents", result["candidate_errors"])
        self.assertEqual(before["calculated_total_cents"], 5430)

    def test_source_conflict_cannot_be_fixed_by_model_claim(self):
        candidate = reconcile(SOURCE)["record"]
        result = validate_candidate(SCENARIOS["mismatch"], candidate)
        self.assertEqual(result["status"], "needs_human_review")
        self.assertTrue(result["source_report"]["record"]["conflict_detected"])
        candidate["stated_total_cents"] = True
        self.assertIn("schema", validate_candidate(SOURCE, candidate)["candidate_errors"])

    def test_empty_or_oversized_input_rejected(self):
        for source in ("", " ", None, "x" * 20001):
            with self.assertRaises(ValueError):
                reconcile(source)

    def test_missing_stated_total_does_not_erase_independent_calculation(self):
        report = reconcile(SOURCE.replace("Total: USD 54.30\n", ""))
        self.assertEqual(report["status"], "needs_human_review")
        self.assertIsNone(report["record"]["stated_total_cents"])
        self.assertEqual(report["record"]["calculated_total_cents"], 5430)
        self.assertIsNone(report["record"]["difference_cents"])

    def test_bare_other_and_duplicate_receipt_ids_remain_unresolved(self):
        report = reconcile(SOURCE.replace("Category: filter", "Category: other"))
        self.assertEqual(report["record"]["category"], "unclear")
        self.assertIn("category_unresolved", report["issues"])
        self.assertIsNone(reconcile(SOURCE + "Receipt: R-4002\n")["record"]["calculated_total_cents"])

    def test_subtotal_conflict_survives_missing_shipping(self):
        source = SOURCE.replace("Subtotal: USD 47.50", "Subtotal: USD 48.50").replace("Shipping: USD 5.00\n", "")
        report = reconcile(source)
        self.assertEqual(report["item_subtotal_cents"], 4750)
        self.assertIsNone(report["record"]["calculated_total_cents"])
        self.assertTrue(report["record"]["conflict_detected"])
        self.assertIn("subtotal_mismatch", report["issues"])
        self.assertIn("missing_or_repeated_shipping", report["issues"])
        self.assertEqual(report["status"], "needs_human_review")
