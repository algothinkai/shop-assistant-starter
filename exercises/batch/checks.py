from copy import deepcopy
import unittest
from .contracts import BatchFailure, bind
from .fixtures import DOCUMENTS, CANDIDATES, succeeded, failure, lines
from .workflow import schedule, reconcile, scale_up, retry_plan

MODEL = "offline-model"
NOTE = "Keep cents as integers and preserve exact labeled evidence."


class BatchChecks(unittest.TestCase):
    def setUp(self):
        self.payload = bind(DOCUMENTS, MODEL, NOTE)
        self.manifest = self.payload["manifest"]
        self.records = [succeeded(d["id"]) for d in DOCUMENTS]

    def test_latency_budget_is_not_a_success_sla(self):
        args = dict(
            blocking=False,
            local_tool_roundtrip=False,
            deadline_hours=30,
            cadence_hours=4,
            recovery_hours=2,
        )
        result = schedule(**args)
        self.assertEqual(result["mode"], "batch_candidate")
        self.assertEqual(result["planned_hours"], 30)
        self.assertFalse(result["guaranteed_completion"])
        for name in ("blocking", "local_tool_roundtrip"):
            self.assertEqual(schedule(**{**args, name: True})["mode"], "synchronous")
        self.assertEqual(
            schedule(**{**args, "deadline_hours": 29})["mode"], "deadline_not_supported"
        )
        for value in (True, float("nan"), -1):
            with self.assertRaises(BatchFailure):
                schedule(**{**args, "cadence_hours": value})

    def test_request_binding_rejects_duplicate_or_changed_documents(self):
        with self.assertRaises(BatchFailure):
            bind([DOCUMENTS[0], DOCUMENTS[0]], MODEL, NOTE)
        changed = deepcopy(self.manifest)
        changed["documents"][0]["source"] += "changed"
        with self.assertRaises(BatchFailure):
            reconcile(changed, lines(self.records), "ended")

    def test_reordered_results_join_by_id_not_position(self):
        result = reconcile(self.manifest, lines(list(reversed(self.records))), "ended")
        self.assertTrue(result["all_validated"])
        self.assertEqual(
            result["outcomes"]["receipt-1001"]["candidate"]["total_cents"]["value"],
            4200,
        )
        self.assertEqual(
            result["outcomes"]["receipt-1002"]["candidate"]["total_cents"]["value"],
            12900,
        )

    def test_duplicate_unknown_ids_and_duplicate_json_keys_are_rejected(self):
        for records in [
            self.records + [self.records[0]],
            [{**self.records[0], "custom_id": "unknown"}],
        ]:
            with self.assertRaises(BatchFailure):
                reconcile(self.manifest, lines(records), "ended")
        with self.assertRaises(BatchFailure):
            reconcile(
                self.manifest, '{"custom_id":"a","custom_id":"b","result":{}}', "ended"
            )

    def test_pending_or_missing_records_cannot_trigger_resubmission(self):
        with self.assertRaises(BatchFailure):
            reconcile(self.manifest, lines(self.records), "in_progress")
        result = reconcile(self.manifest, lines(self.records[:-1]), "ended")
        self.assertFalse(result["complete_import"])
        self.assertEqual(result["missing_ids"], ["receipt-1002"])
        with self.assertRaises(BatchFailure):
            retry_plan(self.manifest, lines(self.records[:-1]))

    def test_provider_success_does_not_override_source_or_terminal_validation(self):
        bad = deepcopy(CANDIDATES["receipt-1003"])
        bad["total_cents"]["value"] = 76
        records = [succeeded("receipt-1003", bad), *self.records[1:]]
        result = reconcile(self.manifest, lines(records), "ended")
        self.assertEqual(result["outcomes"]["receipt-1003"]["status"], "needs_repair")
        for stop in ("max_tokens", "pause_turn", "end_turn"):
            changed = deepcopy(self.records)
            changed[0]["result"]["message"]["stop_reason"] = stop
            self.assertEqual(
                reconcile(self.manifest, lines(changed), "ended")["outcomes"][
                    "receipt-1003"
                ]["status"],
                "needs_repair",
            )

    def test_sample_failure_blocks_scale_up_and_success_excludes_sample_ids(self):
        sample = bind(DOCUMENTS[:2], MODEL, NOTE)["manifest"]
        bad = deepcopy(CANDIDATES["receipt-1003"])
        bad["total_cents"]["value"] = 76
        result = scale_up(
            self.payload,
            sample,
            lines([succeeded("receipt-1003", bad), self.records[1]]),
            evidence_mode="authored_fixture",
        )
        self.assertEqual(result["status"], "refine_sample_first")
        self.assertIsNone(result["remaining"])
        result = scale_up(
            self.payload,
            sample,
            lines(self.records[:2]),
            evidence_mode="authored_fixture",
        )
        self.assertEqual(result["status"], "sample_passed")
        self.assertEqual(
            [d["id"] for d in result["remaining"]["manifest"]["documents"]],
            ["receipt-1002"],
        )
        self.assertEqual(result["evidence_mode"], "authored_fixture")

    def test_sample_cannot_authorize_changed_prompt_model_source_or_payload(self):
        for model, note in [
            ("different-model", NOTE),
            (MODEL, "Changed quality instruction"),
        ]:
            sample = bind(DOCUMENTS[:2], model, note)["manifest"]
            with self.assertRaises(BatchFailure):
                scale_up(
                    self.payload,
                    sample,
                    lines(self.records[:2]),
                    evidence_mode="local_model_output",
                )
        docs = deepcopy(DOCUMENTS[:2])
        docs[0]["source"] += "changed"
        with self.assertRaises(BatchFailure):
            scale_up(
                self.payload,
                bind(docs, MODEL, NOTE)["manifest"],
                lines(self.records[:2]),
                evidence_mode="authored_fixture",
            )
        payload = deepcopy(self.payload)
        payload["body"]["requests"][0]["params"]["max_tokens"] = 999
        with self.assertRaises(BatchFailure):
            scale_up(
                payload,
                bind(DOCUMENTS[:2], MODEL, NOTE)["manifest"],
                lines(self.records[:2]),
                evidence_mode="authored_fixture",
            )

    def test_retry_selects_transient_expired_only_and_keeps_validated(self):
        records = [
            self.records[0],
            failure("receipt-1001"),
            failure("receipt-1002", "expired"),
        ]
        result = retry_plan(self.manifest, lines(records))
        self.assertEqual(
            [d["id"] for d in result["payload"]["manifest"]["documents"]],
            ["receipt-1001", "receipt-1002"],
        )
        self.assertEqual(result["retained_validated_ids"], ["receipt-1003"])
        self.assertEqual(result["parent_body_sha256"], self.manifest["body_sha256"])

    def test_canceled_invalid_and_nontransient_errors_need_review(self):
        records = [
            failure("receipt-1003", "canceled"),
            failure("receipt-1001", error_type="invalid_request_error"),
            failure("receipt-1002", error_type="authentication_error"),
        ]
        result = retry_plan(self.manifest, lines(records))
        self.assertIsNone(result["payload"])
        self.assertEqual(len(result["held_for_review"]), 3)

    def test_explicit_chunk_repair_preserves_full_source_and_lineage(self):
        records = [
            failure("receipt-1003", error_type="invalid_request_error"),
            *self.records[1:],
        ]
        source = DOCUMENTS[0]["source"]
        split = source.index("Total:")
        chunks = {"receipt-1003": [source[:split], source[split:]]}
        result = retry_plan(self.manifest, lines(records), chunks=chunks)
        self.assertTrue(result["sample_review_required"])
        self.assertEqual(
            "".join(d["source"] for d in result["payload"]["manifest"]["documents"]),
            source,
        )
        self.assertTrue(
            all(x["parent_id"] == "receipt-1003" for x in result["lineage"].values())
        )
        self.assertEqual(
            result["retained_validated_ids"], ["receipt-1001", "receipt-1002"]
        )
        for invalid in [
            {"receipt-1001": ["x", "y"]},
            {"receipt-1003": [source[:split], "truncated"]},
            {"unknown": ["a", "b"]},
        ]:
            with self.assertRaises(BatchFailure):
                retry_plan(self.manifest, lines(records), chunks=invalid)

    def test_input_data_stays_unchanged(self):
        before = deepcopy(self.manifest)
        records = deepcopy(self.records)
        result = reconcile(self.manifest, lines(self.records), "ended")
        result["outcomes"]["receipt-1003"]["candidate"]["total_cents"]["value"] = 99
        self.assertEqual(self.manifest, before)
        self.assertEqual(self.records, records)

    def test_duplicate_source_copies_do_not_fill_two_document_sample(self):
        docs = [
            DOCUMENTS[0],
            {"id": "copied-receipt", "source": DOCUMENTS[0]["source"]},
            DOCUMENTS[1],
        ]
        payload = bind(docs, MODEL, NOTE)
        sample = bind(docs[:2], MODEL, NOTE)["manifest"]
        copied = {**succeeded("receipt-1003"), "custom_id": "copied-receipt"}
        with self.assertRaises(BatchFailure):
            scale_up(
                payload,
                sample,
                lines([self.records[0], copied]),
                evidence_mode="authored_fixture",
            )

    def test_chunk_ids_cannot_replace_existing_success_or_retry(self):
        from .contracts import digest

        collision = "chunk_" + digest("receipt-1003")[:12] + "_1"
        docs = [
            DOCUMENTS[0],
            {"id": collision, "source": DOCUMENTS[1]["source"]},
            {"id": collision + "_r1", "source": DOCUMENTS[2]["source"]},
        ]
        payload = bind(docs, MODEL, NOTE)
        records = [
            failure("receipt-1003", error_type="invalid_request_error"),
            {**succeeded("receipt-1001"), "custom_id": collision},
            failure(collision + "_r1", "expired"),
        ]
        source = DOCUMENTS[0]["source"]
        split = source.index("Total:")
        result = retry_plan(
            payload["manifest"],
            lines(records),
            chunks={"receipt-1003": [source[:split], source[split:]]},
        )
        ids = [r["custom_id"] for r in result["payload"]["body"]["requests"]]
        self.assertNotIn(collision, ids)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(collision + "_r1", ids)
        chunks = [
            cid
            for cid, x in result["lineage"].items()
            if x["parent_id"] == "receipt-1003"
        ]
        self.assertTrue(set(chunks).isdisjoint(d["id"] for d in docs))
        self.assertEqual(result["retained_validated_ids"], [collision])
