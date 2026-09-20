"""Reconstruct source-bound chunk proposals for review, never automatic acceptance."""

from copy import deepcopy
from exercises.batch.contracts import BatchFailure, digest
from exercises.batch.workflow import retry_plan, reconcile
from exercises.extraction.schema import FIELDS
from exercises.extraction.validation import validate


def reconstruct(manifest, original_results, chunks, retry_results, *, evidence_mode):
    if evidence_mode not in ("authored_fixture", "local_model_output"):
        raise BatchFailure("declare_result_provenance")
    if not isinstance(chunks, dict) or not chunks:
        raise BatchFailure("explicit_chunk_repair_required")
    plan = retry_plan(manifest, original_results, chunks=chunks)
    retried = reconcile(plan["payload"]["manifest"], retry_results, "ended")
    if not retried["complete_import"]:
        raise BatchFailure("incomplete_chunk_results")
    originals = {d["id"]: d["source"] for d in manifest["documents"]}
    parents = {}
    for parent in chunks:
        children = sorted(
            (
                (cid, info["source_part"])
                for cid, info in plan["lineage"].items()
                if info["parent_id"] == parent
            ),
            key=lambda item: item[1],
        )
        evidence = {field: [] for field in FIELDS}
        problems = []
        for cid, part in children:
            outcome = retried["outcomes"][cid]
            if "candidate" not in outcome or outcome["validation"]["errors"]:
                problems.append(
                    {
                        "child_id": cid,
                        "reason": "invalid_or_failed_chunk",
                        "outcome": deepcopy(outcome),
                    }
                )
                continue
            for field, item in outcome["candidate"].items():
                if item["value"] is not None:
                    evidence[field].append(
                        {"child_id": cid, "source_part": part, **deepcopy(item)}
                    )
        conflicts = [
            field
            for field, items in evidence.items()
            if len({digest(item["value"]) for item in items}) > 1
        ]
        candidate = None
        validation = None
        if not conflicts and not problems:
            candidate = {
                field: {"value": items[0]["value"], "evidence": items[0]["evidence"]}
                if items
                else {"value": None, "evidence": None}
                for field, items in evidence.items()
            }
            validation = validate(originals[parent], candidate)
        ready = (
            validation is not None
            and not validation["errors"]
            and not validation["missing_fields"]
        )
        parents[parent] = {
            "status": "ready_for_review" if ready else "needs_review",
            "accepted": False,
            "candidate": candidate,
            "field_evidence": evidence,
            "conflicting_fields": conflicts,
            "chunk_problems": problems,
            "validation": validation,
            "source_sha256": digest(originals[parent]),
        }
    return {
        "parents": parents,
        "parent_body_sha256": manifest["body_sha256"],
        "retry_body_sha256": plan["payload"]["manifest"]["body_sha256"],
        "original_results_sha256": digest(original_results),
        "retry_results_sha256": digest(retry_results),
        "lineage": plan["lineage"],
        "retained_validated_ids": plan["retained_validated_ids"],
        "held_for_review": plan["held_for_review"],
        "original_outcomes": reconcile(manifest, original_results, "ended")["outcomes"],
        "retry_outcomes": retried["outcomes"],
        "evidence_mode": evidence_mode,
        "limitation": "Provenance is caller supplied. Reconstruction does not prove live model quality or authorize document acceptance.",
    }
