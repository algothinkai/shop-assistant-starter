"""Implement batch scheduling, sample gating, result matching and failed-only retries."""


def schedule(
    *, blocking, local_tool_roundtrip, deadline_hours, cadence_hours, recovery_hours
):
    raise NotImplementedError("Choose a workflow from its latency constraints")


def reconcile(manifest, jsonl, processing_status):
    raise NotImplementedError(
        "Join result records by custom_id and validate source evidence"
    )


def scale_up(payload, sample_manifest, sample_jsonl, *, evidence_mode):
    raise NotImplementedError("Require a matching small-sample check before scaling")


def retry_plan(manifest, jsonl, *, chunks=None):
    raise NotImplementedError("Retry failed IDs only and preserve repair lineage")
