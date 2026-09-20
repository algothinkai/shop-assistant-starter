"""Stage 1 reference: summarize only the requested local run."""


def summarize_run(events, run_id):
    """Use ordered trusted local events; missing terminal evidence is incomplete."""
    calls = errors = 0
    status = "incomplete"
    for event in events:
        if event["run_id"] != run_id:
            continue
        if event["kind"] == "call":
            calls += 1
        elif event["kind"] == "error":
            errors += 1
        elif event["kind"] == "demo_outcome":
            status = event["detail"]["status"]
    return {"run_id": run_id, "calls": calls, "errors": errors, "status": status}
