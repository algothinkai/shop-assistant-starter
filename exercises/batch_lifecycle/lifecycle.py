"""Durable single-job lifecycle. Uncertain POST outcomes are never replayed."""

from copy import deepcopy
from exercises.batch.contracts import BatchFailure, checked, digest
from exercises.batch.workflow import reconcile
from .transport import batch_id

KINDS = ("processing", "succeeded", "errored", "canceled", "expired")


def snapshot(value, count, identifier=None):
    if not isinstance(value, dict) or value.get("type") != "message_batch":
        raise BatchFailure("invalid_provider_snapshot")
    identifier_value = batch_id(value.get("id"))
    counts = value.get("request_counts")
    status = value.get("processing_status")
    if (
        identifier is not None
        and identifier_value != identifier
        or status not in ("in_progress", "canceling", "ended")
        or not isinstance(counts, dict)
        or set(counts) != set(KINDS)
        or any(type(v) is not int or v < 0 for v in counts.values())
        or sum(counts.values()) != count
        or status == "ended"
        and counts["processing"] != 0
    ):
        raise BatchFailure("invalid_provider_snapshot")
    return {
        "type": "message_batch",
        "id": identifier_value,
        "processing_status": status,
        "request_counts": deepcopy(counts),
    }


def result_record(state, raw):
    report = reconcile(state["manifest"], raw, "ended")
    if not report["complete_import"]:
        raise BatchFailure("incomplete_results")
    counts = {key: 0 for key in KINDS}
    for outcome in report["outcomes"].values():
        counts[outcome["provider_type"]] += 1
    if counts != state["provider"]["request_counts"]:
        raise BatchFailure("result_counts_mismatch")
    return {
        "provider_id": state["provider"]["id"],
        "jsonl": raw,
        "sha256": digest(raw),
        "report": report,
    }


def read(store, transport):
    if transport.mode not in ("authored_transport", "live_http"):
        raise BatchFailure("invalid_transport_mode")
    state = store.read()
    if state is None:
        return None
    if state["mode"] != transport.mode:
        raise BatchFailure("transport_mode_changed")
    if state["status"] == "submission_unknown":
        if state["provider"] is not None or state["results"] is not None:
            raise BatchFailure("invalid_unknown_state")
        return state
    provider = snapshot(state["provider"], len(state["manifest"]["documents"]))
    if provider != state["provider"]:
        raise BatchFailure("invalid_stored_provider")
    ended = provider["processing_status"] == "ended"
    if ended != (state["status"] in ("ended", "collected")):
        raise BatchFailure("inconsistent_job_status")
    if state["status"] == "collected":
        results = state["results"]
        if (
            not isinstance(results, dict)
            or result_record(state, results.get("jsonl")) != results
        ):
            raise BatchFailure("invalid_cached_results")
    elif state["results"] is not None:
        raise BatchFailure("unexpected_results")
    return state


def submit(store, payload, transport):
    if not isinstance(payload, dict) or set(payload) != {"body", "manifest"}:
        raise BatchFailure("invalid_payload")
    if checked(payload["manifest"]) != payload:
        raise BatchFailure("changed_payload")
    with store.locked():
        state = read(store, transport)
        if state is not None:
            if state["manifest"] != payload["manifest"]:
                raise BatchFailure("job_already_bound")
            if state["status"] == "submission_unknown":
                raise BatchFailure("unresolved_submission")
            return state
        state = {
            "version": 1,
            "mode": transport.mode,
            "status": "submission_unknown",
            "manifest": deepcopy(payload["manifest"]),
            "provider": None,
            "results": None,
        }
        store.write(state)
        provider = snapshot(
            transport.create(payload["body"]), len(payload["manifest"]["documents"])
        )
        state["provider"] = provider
        state["status"] = (
            "ended" if provider["processing_status"] == "ended" else "submitted"
        )
        store.write(state)
        return state


def known(store, transport):
    state = read(store, transport)
    if state is None:
        raise BatchFailure("job_not_found")
    if state["status"] == "submission_unknown":
        raise BatchFailure("unresolved_submission")
    return state


def refresh(store, transport):
    with store.locked():
        state = known(store, transport)
        if state["status"] == "collected":
            return state
        provider = snapshot(
            transport.retrieve(state["provider"]["id"]),
            len(state["manifest"]["documents"]),
            state["provider"]["id"],
        )
        if state["status"] == "ended" and provider["processing_status"] != "ended":
            raise BatchFailure("provider_status_regressed")
        state["provider"] = provider
        state["status"] = (
            "ended" if provider["processing_status"] == "ended" else "submitted"
        )
        store.write(state)
        return state


def collect(store, transport):
    with store.locked():
        state = known(store, transport)
        if state["status"] == "collected":
            return state
        if state["status"] != "ended":
            raise BatchFailure("batch_not_ended")
        state["results"] = result_record(
            state, transport.results(state["provider"]["id"])
        )
        state["status"] = "collected"
        store.write(state)
        return state
