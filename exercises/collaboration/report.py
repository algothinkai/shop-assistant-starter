"""Stage 1 exercise: the implementation intentionally violates the contract."""


def summarize_run(events, run_id):
    """Summarize one ordered local run without mutating the events.

    Return run_id, calls, errors and status. Status is the final demo_outcome
    status, or incomplete if that run has no terminal outcome. Never guess
    completion from a successful tool result. Input is trusted local events.
    """
    return {
        "run_id": run_id,
        "calls": sum(event["kind"] == "call" for event in events),
        "errors": sum(event["kind"] == "error" for event in events),
        "status": "completed",
    }
