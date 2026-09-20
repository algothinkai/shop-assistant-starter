"""Bounded batch planning and source-validated results, not a hosted job runner."""

from copy import deepcopy
import math
from .contracts import BatchFailure, bind, checked, parse, digest
from exercises.extraction_messages.adapter import read_candidate, ExtractionFailure
from exercises.extraction.validation import validate


def schedule(
    *, blocking, local_tool_roundtrip, deadline_hours, cadence_hours, recovery_hours
):
    if type(blocking) is not bool or type(local_tool_roundtrip) is not bool:
        raise BatchFailure("invalid_latency_requirement")
    for value in (deadline_hours, cadence_hours, recovery_hours):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise BatchFailure("invalid_latency_requirement")
    if not deadline_hours or not cadence_hours:
        raise BatchFailure("invalid_latency_requirement")
    planned = cadence_hours + 24 + recovery_hours
    mode = (
        "synchronous"
        if blocking or local_tool_roundtrip
        else "batch_candidate"
        if planned <= deadline_hours
        else "deadline_not_supported"
    )
    return {
        "mode": mode,
        "planned_hours": planned,
        "processing_assumption_hours": 24,
        "guaranteed_completion": False,
        "reason": "Batch expiry is not guaranteed successful completion; allow recovery or use a suitable synchronous workflow.",
    }


def reconcile(manifest, jsonl, processing_status):
    checked(manifest)
    if processing_status != "ended":
        raise BatchFailure("batch_not_ended")
    if not isinstance(jsonl, str) or len(jsonl.encode()) > 2000000:
        raise BatchFailure("invalid_results")
    docs = {d["id"]: d for d in manifest["documents"]}
    records = {}
    for line in jsonl.splitlines():
        if not line.strip():
            continue
        row = parse(line)
        if not isinstance(row, dict) or set(row) != {"custom_id", "result"}:
            raise BatchFailure("invalid_result_record")
        cid = row["custom_id"]
        if not isinstance(cid, str) or cid not in docs or cid in records:
            raise BatchFailure("unknown_or_duplicate_result_id")
        result = row["result"]
        if not isinstance(result, dict):
            raise BatchFailure("invalid_result_record")
        kind = result.get("type")
        value = {"status": "needs_review", "provider_type": kind}
        if kind == "succeeded" and set(result) == {"type", "message"}:
            try:
                candidate = read_candidate(result["message"])
            except ExtractionFailure:
                value.update(
                    status="needs_repair", reason="incomplete_or_unsupported_message"
                )
            else:
                validation = validate(docs[cid]["source"], candidate)
                source_problem = any(
                    e["kind"] in ("source_conflict", "source_unresolved")
                    for e in validation["errors"]
                )
                status = (
                    "needs_review"
                    if source_problem or validation["missing_fields"]
                    else "needs_repair"
                    if validation["errors"]
                    else "validated"
                )
                value.update(status=status, candidate=candidate, validation=validation)
        elif kind == "errored" and set(result) == {"type", "error"}:
            error = result["error"]
            if (
                not isinstance(error, dict)
                or error.get("type") != "error"
                or not isinstance(error.get("error"), dict)
                or not isinstance(error["error"].get("type"), str)
            ):
                raise BatchFailure("invalid_error_record")
            error_type = error["error"]["type"]
            if error_type in ("api_error", "overloaded_error", "rate_limit_error"):
                value.update(status="retryable", reason=error_type)
            elif error_type == "invalid_request_error":
                value.update(status="needs_repair", reason="invalid_request")
            else:
                value.update(
                    status="needs_review", reason="non_transient_provider_error"
                )
        elif kind in ("expired", "canceled") and set(result) == {"type"}:
            value.update(
                status="retryable" if kind == "expired" else "needs_review", reason=kind
            )
        else:
            raise BatchFailure("invalid_result_type")
        records[cid] = value
    missing = sorted(set(docs) - set(records))
    for cid in missing:
        records[cid] = {
            "status": "missing",
            "reason": "retrieve_complete_results_before_retry",
        }
    return {
        "body_sha256": manifest["body_sha256"],
        "complete_import": not missing,
        "all_validated": not missing
        and all(r["status"] == "validated" for r in records.values()),
        "missing_ids": missing,
        "outcomes": {cid: records[cid] for cid in docs},
    }


def scale_up(payload, sample_manifest, sample_jsonl, *, evidence_mode):
    if evidence_mode not in ("authored_fixture", "local_model_output"):
        raise BatchFailure("declare_sample_provenance")
    if not isinstance(payload, dict) or set(payload) != {"body", "manifest"}:
        raise BatchFailure("invalid_payload")
    expected = checked(payload["manifest"])
    if payload != expected:
        raise BatchFailure("changed_payload")
    checked(sample_manifest)
    full = payload["manifest"]
    if any(sample_manifest[k] != full[k] for k in ("model", "prompt_note")):
        raise BatchFailure("sample_configuration_changed")
    documents = {d["id"]: d for d in full["documents"]}
    sample = sample_manifest["documents"]
    if len({digest(d["source"].strip()) for d in sample}) < min(
        2, len(documents)
    ) or any(documents.get(d["id"]) != d for d in sample):
        raise BatchFailure("sample_not_bound_to_documents")
    checked_sample = reconcile(sample_manifest, sample_jsonl, "ended")
    if not checked_sample["all_validated"]:
        return {
            "status": "refine_sample_first",
            "sample": checked_sample,
            "remaining": None,
            "evidence_mode": evidence_mode,
        }
    used = {d["id"] for d in sample}
    remaining = [d for d in full["documents"] if d["id"] not in used]
    return {
        "status": "sample_passed",
        "sample": checked_sample,
        "remaining": bind(remaining, full["model"], full["prompt_note"])
        if remaining
        else None,
        "evidence_mode": evidence_mode,
        "limitation": "A small source-validated sample is not representative model-quality proof; local output provenance is caller supplied.",
    }


def retry_plan(manifest, jsonl, *, chunks=None):
    result = reconcile(manifest, jsonl, "ended")
    if not result["complete_import"]:
        raise BatchFailure("incomplete_import_no_retry")
    if chunks is None:
        chunks = {}
    if not isinstance(chunks, dict):
        raise BatchFailure("invalid_repairs")
    docs = {d["id"]: d for d in manifest["documents"]}
    if any(cid not in docs for cid in chunks):
        raise BatchFailure("unknown_repair_id")
    retry = []
    reserved_ids = set(docs)
    lineage = {}
    held = []
    for cid, outcome in result["outcomes"].items():
        if cid in chunks:
            pieces = chunks[cid]
            if (
                outcome.get("reason") != "invalid_request"
                or not isinstance(pieces, list)
                or not 2 <= len(pieces) <= 4
                or any(not isinstance(p, str) or not p.strip() for p in pieces)
                or "".join(pieces) != docs[cid]["source"]
            ):
                raise BatchFailure("repair_must_partition_failed_source_exactly")
            for index, piece in enumerate(pieces, 1):
                base_id = "chunk_" + digest(cid)[:12] + "_" + str(index)
                child = base_id
                suffix = 0
                while child in reserved_ids:
                    suffix += 1
                    child = base_id + "_r" + str(suffix)
                reserved_ids.add(child)
                retry.append({"id": child, "source": piece})
                lineage[child] = {
                    "parent_id": cid,
                    "source_part": index,
                    "reason": "explicit_context_repair",
                }
        elif outcome["status"] == "retryable":
            retry.append(deepcopy(docs[cid]))
            lineage[cid] = {"parent_id": cid, "reason": outcome["reason"]}
        elif outcome["status"] != "validated":
            held.append(cid)
    return {
        "payload": bind(retry, manifest["model"], manifest["prompt_note"])
        if retry
        else None,
        "parent_body_sha256": manifest["body_sha256"],
        "lineage": lineage,
        "held_for_review": held,
        "retained_validated_ids": [
            cid for cid, o in result["outcomes"].items() if o["status"] == "validated"
        ],
        "sample_review_required": bool(chunks),
        "warning": "Chunking can split required receipt facts. Review extraction and merge evidence before accepting a document; no automatic merged success.",
    }
