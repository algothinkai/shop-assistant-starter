"""Check format/provenance mechanics and example separation, never model quality."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from ..extraction.pipeline import extract
from ..extraction.fixtures import SOURCE, CANDIDATE, authored_generator
from .adapter import validate, build_request

ROOT = Path(__file__).parent


def transfer():
    return json.loads((ROOT / "transfer.json").read_text())


class FormatChecks(unittest.TestCase):
    def test_three_examples_and_transfer_have_supported_values(self):
        examples = json.loads((ROOT / "examples.json").read_text())
        self.assertEqual(len(examples), 3)
        for example in examples + [transfer()]:
            self.assertEqual(validate(example["source"], example["candidate"])["errors"], [])
        self.assertTrue(all(e["reason"] for e in examples))

    def test_existing_labeled_contract_is_preserved(self):
        self.assertEqual(validate(SOURCE, CANDIDATE), {"errors": [], "missing_fields": []})

    def test_missing_customer_not_filled_from_examples(self):
        case = json.loads((ROOT / "examples.json").read_text())[2]
        self.assertEqual(validate(case["source"], case["candidate"])["missing_fields"], ["customer_name"])
        case["candidate"]["customer_name"] = {"value": "Mina Reed", "evidence": "Customer: Mina Reed"}
        self.assertTrue(validate(case["source"], case["candidate"])["errors"])

    def test_inline_normalization_does_not_replace_original_evidence(self):
        case = transfer(); before = deepcopy(case)
        self.assertEqual(validate(case["source"], case["candidate"])["errors"], [])
        self.assertEqual(case, before)
        case["candidate"]["customer_name"]["evidence"] = "Customer: Tess Lane"
        self.assertTrue(validate(case["source"], case["candidate"])["errors"])

    def test_truncated_row_wrong_units_and_borrowed_name_fail(self):
        for field, value in [("total_cents", 57), ("customer_name", "Tess"), ("order_id", "O-3001")]:
            case = transfer();case["candidate"][field]["value"] = value
            self.assertTrue(validate(case["source"], case["candidate"])["errors"])
        case = transfer();case["candidate"]["total_cents"]["evidence"] = "USD 57.25"
        self.assertTrue(validate(case["source"], case["candidate"])["errors"])

    def test_invalid_inline_date_and_extra_column_need_review(self):
        for source in [transfer()["source"].replace("2026-09-02", "2026-02-30"), transfer()["source"] + " | total=USD 1.00"]:
            case = transfer(); candidate = {k: {"value": None, "evidence": None} for k in case["candidate"]}
            result = extract(source, authored_generator([candidate], []), mode="authored_fixture_no_model", validator=validate)
            self.assertEqual(result["status"], "needs_human_review")
            self.assertEqual(result["review_reason"], "source_unresolved")
            self.assertEqual(len(result["attempts"]), 1)

    def test_conflicting_labeled_and_inline_totals_are_not_hidden(self):
        case = transfer(); source = case["source"] + "\nTotal: USD 1.00"
        report = validate(source, case["candidate"])
        self.assertTrue(any(e["kind"] == "source_conflict" for e in report["errors"]))

    def test_schema_failure_still_reports_error(self):
        case = transfer();case["candidate"]["total_cents"]["value"] = True
        self.assertTrue(validate(case["source"], case["candidate"])["errors"])

    def test_few_shot_examples_do_not_replace_current_request(self):
        case = transfer();request = {"source": case["source"], "failed_candidate": None, "validation_errors": []}
        before = deepcopy(request);payload = build_request("test", request)
        self.assertEqual(json.loads(payload["messages"][0]["content"]), request)
        self.assertEqual(request, before)
        self.assertIn("<examples>", payload["system"])
        self.assertEqual(payload["system"].count("<example>"), 3)
        self.assertNotIn("Tess Lane", payload["system"])
        self.assertTrue(payload["tools"][0]["strict"])
        self.assertIn("inline row", payload["tools"][0]["description"])

    def test_current_receipt_correction_retains_source_not_examples(self):
        case = transfer();bad = deepcopy(case["candidate"]);bad["total_cents"]["value"] = 57
        requests = []
        result = extract(case["source"], authored_generator([bad, case["candidate"]], requests), mode="authored_fixture_no_model", validator=validate)
        self.assertEqual(result["status"], "validated_candidate")
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[1]["source"], case["source"])
        self.assertTrue(requests[1]["validation_errors"])
        self.assertEqual(result["candidate"]["total_cents"]["evidence"], case["source"])
