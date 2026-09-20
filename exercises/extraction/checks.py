"""Risk-based receipt contract and correction checks; no model calls."""
import copy
import unittest
from .fixtures import SOURCE, CANDIDATE, authored_generator
from .validation import validate
from .pipeline import extract


class ExtractionChecks(unittest.TestCase):
    def test_valid_candidate_preserves_input(self):
        candidate = copy.deepcopy(CANDIDATE)
        self.assertEqual(validate(SOURCE, candidate), {"errors": [], "missing_fields": []})
        self.assertEqual(candidate, CANDIDATE)

    def test_bool_amount_and_unknown_fields_are_schema_errors(self):
        for change in (lambda x: x["total_cents"].update(value=True), lambda x: x.update(extra="ignored")):
            candidate = copy.deepcopy(CANDIDATE); change(candidate)
            result = validate(SOURCE, candidate)
            self.assertTrue(result["errors"])
            self.assertEqual(result["errors"][0]["kind"], "schema")

    def test_schema_valid_wrong_amount_is_semantic_error(self):
        candidate = copy.deepcopy(CANDIDATE); candidate["total_cents"]["value"] = 7601
        errors = validate(SOURCE, candidate)["errors"]
        self.assertTrue(any(x["field"] == "total_cents" and x["kind"] == "semantic" for x in errors))

    def test_fabricated_quote_and_wrong_field_placement_fail(self):
        candidate = copy.deepcopy(CANDIDATE); candidate["customer_name"] = {"value": "Noor Patel", "evidence": "Noor Patel invented line"}
        self.assertTrue(validate(SOURCE, candidate)["errors"])
        candidate = copy.deepcopy(CANDIDATE); candidate["order_id"] = {"value": "R-1003", "evidence": "Receipt: R-1003"}
        self.assertTrue(validate(SOURCE, candidate)["errors"])

    def test_invalid_calendar_date_fails_even_if_quoted(self):
        source = SOURCE.replace("2026-08-28", "2026-02-31")
        candidate = copy.deepcopy(CANDIDATE); candidate["purchase_date"] = {"value": "2026-02-31", "evidence": "Date: 2026-02-31"}
        self.assertTrue(validate(source, candidate)["errors"])

    def test_missing_value_routes_review_without_retry(self):
        candidate = copy.deepcopy(CANDIDATE); candidate["customer_name"] = {"value": None, "evidence": None}
        source = SOURCE.replace("Customer: Noor Patel\n", "")
        requests = []
        result = extract(source, authored_generator([candidate], requests), mode="authored_fixture_no_model")
        self.assertEqual(result["status"], "needs_human_review")
        self.assertEqual(result["missing_fields"], ["customer_name"])
        self.assertEqual(len(requests), 1)

    def test_null_with_fabricated_support_is_invalid(self):
        candidate = copy.deepcopy(CANDIDATE); candidate["customer_name"]["value"] = None
        self.assertTrue(validate(SOURCE, candidate)["errors"])

    def test_retry_contains_original_failed_candidate_and_specific_errors(self):
        bad = copy.deepcopy(CANDIDATE); bad["total_cents"]["value"] = 1
        requests = []
        result = extract(SOURCE, authored_generator([bad, CANDIDATE], requests), mode="authored_fixture_no_model")
        self.assertEqual(result["status"], "validated_candidate")
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[1]["source"], SOURCE)
        self.assertEqual(requests[1]["failed_candidate"], bad)
        self.assertTrue(any(x["field"] == "total_cents" for x in requests[1]["validation_errors"]))
        self.assertEqual(requests[0]["validation_errors"], [])

    def test_limit_and_generator_failure_never_claim_success(self):
        bad = copy.deepcopy(CANDIDATE); bad["total_cents"]["value"] = 1
        requests = []
        result = extract(SOURCE, authored_generator([bad, bad, CANDIDATE], requests), mode="authored_fixture_no_model")
        self.assertEqual(result["status"], "validation_failed"); self.assertEqual(len(requests), 2)
        def fail(request): raise RuntimeError("PRIVATE_GENERATOR_DETAIL")
        result = extract(SOURCE, fail, mode="authored_fixture_no_model")
        self.assertEqual(result["status"], "generation_failed")
        self.assertNotIn("PRIVATE_GENERATOR_DETAIL", str(result))

    def test_conflicting_source_values_go_to_review_without_retries(self):
        requests = []
        result = extract(SOURCE + "\nTotal: USD 99.00\n", authored_generator([CANDIDATE], requests), mode="authored_fixture_no_model")
        self.assertEqual(result["status"], "needs_human_review")
        self.assertEqual(result["review_reason"], "source_conflict")
        self.assertEqual(len(requests), 1)

    def test_present_but_omitted_field_gets_specific_correction(self):
        candidate = copy.deepcopy(CANDIDATE); candidate["customer_name"] = {"value": None, "evidence": None}
        result = validate(SOURCE, candidate)
        self.assertTrue(any(x["field"] == "customer_name" for x in result["errors"]))
        self.assertEqual(result["missing_fields"], [])
