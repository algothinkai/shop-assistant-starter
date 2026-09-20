"""Explicit reconstruction-stage checks with authored provider records."""

from copy import deepcopy
import unittest
from exercises.batch.contracts import BatchFailure
from exercises.batch.fixtures import DOCUMENTS, CANDIDATES, failure, lines
from exercises.batch.workflow import retry_plan
from exercises.extraction.schema import FIELDS
from .merge import reconstruct
from .fixtures import case


class MergeChecks(unittest.TestCase):
    def run_case(self, value):
        m, original, chunks, rows = value
        return reconstruct(
            m, original, chunks, lines(rows), evidence_mode="authored_fixture"
        )

    def test_complementary_fields_reconstruct_but_require_review(self):
        value = case()
        report = self.run_case(value)
        parent = report["parents"][DOCUMENTS[0]["id"]]
        self.assertEqual(parent["status"], "ready_for_review")
        self.assertFalse(parent["accepted"])
        self.assertEqual(parent["candidate"], CANDIDATES[DOCUMENTS[0]["id"]])
        self.assertEqual(report["retained_validated_ids"], [DOCUMENTS[1]["id"]])
        self.assertTrue(all(parent["field_evidence"][field] for field in FIELDS))

    def test_repeated_agreement_retains_both_supporting_parts(self):
        source = DOCUMENTS[0]["source"].replace(
            "Item:", "Item: NOTE\nOrder: O-1003\nItem:", 1
        )
        parent = self.run_case(case(source))["parents"][DOCUMENTS[0]["id"]]
        self.assertEqual(parent["status"], "ready_for_review")
        self.assertEqual(len(parent["field_evidence"]["order_id"]), 2)
        self.assertFalse(parent["accepted"])

    def test_split_labeled_line_requires_repair_not_guessing(self):
        value = case()
        manifest, original, chunks, _ = value
        source = DOCUMENTS[0]["source"]
        cut = source.index("76.00") + 3
        chunks[DOCUMENTS[0]["id"]] = [source[:cut], source[cut:]]
        plan = retry_plan(manifest, original, chunks=chunks)
        rows = []
        from exercises.batch.fixtures import succeeded

        for child in plan["payload"]["manifest"]["documents"]:
            candidate = {
                field: deepcopy(item)
                if item["evidence"] in child["source"]
                else {"value": None, "evidence": None}
                for field, item in CANDIDATES[DOCUMENTS[0]["id"]].items()
            }
            rows.append(succeeded(child["id"], candidate))
        parent = self.run_case((manifest, original, chunks, rows))["parents"][
            DOCUMENTS[0]["id"]
        ]
        self.assertEqual(parent["status"], "needs_review")
        self.assertTrue(parent["chunk_problems"])
        self.assertFalse(parent["accepted"])

    def test_unrepaired_original_failure_remains_in_handoff(self):
        manifest, _, chunks, rows = case()
        original = lines(
            [
                failure(DOCUMENTS[0]["id"], error_type="invalid_request_error"),
                failure(DOCUMENTS[1]["id"], kind="canceled"),
            ]
        )
        report = self.run_case((manifest, original, chunks, rows))
        self.assertEqual(report["held_for_review"], [DOCUMENTS[1]["id"]])
        self.assertEqual(
            report["original_outcomes"][DOCUMENTS[1]["id"]]["reason"], "canceled"
        )
        self.assertEqual(
            report["parents"][DOCUMENTS[0]["id"]]["status"], "ready_for_review"
        )

    def test_reordering_output_does_not_reorder_source_parts(self):
        value = case()
        expected = self.run_case(value)["parents"]
        value[-1].reverse()
        self.assertEqual(self.run_case(value)["parents"], expected)

    def test_missing_duplicate_unknown_results_rejected(self):
        for variant in ("missing", "duplicate", "unknown"):
            value = case()
            rows = value[-1]
            if variant == "missing":
                rows.pop()
            elif variant == "duplicate":
                rows.append(deepcopy(rows[0]))
            else:
                rows[0]["custom_id"] = "unrelated"
            with self.assertRaises(BatchFailure):
                self.run_case(value)

    def test_foreign_chunk_evidence_blocks_reconstruction(self):
        value = case()
        value[-1][0]["result"]["message"]["content"][0]["input"]["total_cents"] = (
            deepcopy(CANDIDATES[DOCUMENTS[0]["id"]]["total_cents"])
        )
        parent = self.run_case(value)["parents"][DOCUMENTS[0]["id"]]
        self.assertEqual(parent["status"], "needs_review")
        self.assertIsNone(parent["candidate"])
        self.assertTrue(parent["chunk_problems"])

    def test_conflicting_valid_chunk_values_preserve_both(self):
        source = DOCUMENTS[0]["source"].replace("Item:", "Order: O-9999\nItem:")
        value = case(source)
        # Split between contradictory full lines, so each local chunk is coherent.
        m, original, chunks, rows = value
        cut = source.index("Order: O-9999")
        chunks[DOCUMENTS[0]["id"]] = [source[:cut], source[cut:]]
        plan = retry_plan(m, original, chunks=chunks)
        rows[1]["result"]["message"]["content"][0]["input"]["order_id"] = {
            "value": "O-9999",
            "evidence": "Order: O-9999",
        }
        self.assertEqual(len(plan["lineage"]), 2)
        parent = self.run_case(value)["parents"][DOCUMENTS[0]["id"]]
        self.assertIn("order_id", parent["conflicting_fields"])
        self.assertEqual(len(parent["field_evidence"]["order_id"]), 2)
        self.assertIsNone(parent["candidate"])
        self.assertFalse(parent["accepted"])

    def test_missing_whole_document_field_stays_missing(self):
        source = DOCUMENTS[0]["source"].replace("Customer: Noor Patel\n", "")
        parent = self.run_case(case(source))["parents"][DOCUMENTS[0]["id"]]
        self.assertEqual(parent["status"], "needs_review")
        self.assertIn("customer_name", parent["validation"]["missing_fields"])

    def test_failed_chunk_does_not_produce_partial_success(self):
        value = case()
        value[-1][1] = failure(value[-1][1]["custom_id"], kind="expired")
        parent = self.run_case(value)["parents"][DOCUMENTS[0]["id"]]
        self.assertIsNone(parent["candidate"])
        self.assertEqual(parent["status"], "needs_review")

    def test_changed_partition_or_provenance_is_rejected_and_inputs_preserved(self):
        value = case()
        before = deepcopy(value)
        self.run_case(value)
        self.assertEqual(value, before)
        m, original, chunks, rows = value
        with self.assertRaises(BatchFailure):
            reconstruct(
                m, original, chunks, lines(rows), evidence_mode="certified_live"
            )
        chunks[DOCUMENTS[0]["id"]][0] += "invented"
        with self.assertRaises(BatchFailure):
            self.run_case(value)


if __name__ == "__main__":
    unittest.main()
