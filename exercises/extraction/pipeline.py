"""Bounded correction controller. The supplied generator must identify its mode."""
from copy import deepcopy
from .validation import validate


def extract(source, generate, *, mode, max_attempts=2):
    if not isinstance(source, str) or not source.strip():
        raise ValueError("A nonempty source text is required")
    if mode not in ("authored_fixture_no_model", "live_model"):
        raise ValueError("Explicit generator mode required")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 2:
        raise ValueError("Use one or two bounded attempts")
    history = []
    request = {"source": source, "failed_candidate": None, "validation_errors": []}
    for _ in range(max_attempts):
        try:
            candidate = generate(deepcopy(request))
        except Exception:
            return {"mode": mode, "status": "generation_failed", "attempts": history,
                    "message": "Generator failed; no extraction success is claimed."}
        report = validate(source, candidate)
        history.append({"candidate": deepcopy(candidate), "validation": deepcopy(report)})
        source_issue = next((error["kind"] for error in report["errors"] if error["kind"] in ("source_conflict", "source_unresolved")), None)
        if source_issue:
            return {"mode": mode, "status": "needs_human_review", "candidate": deepcopy(candidate),
                    "attempts": history, "review_reason": source_issue}
        if not report["errors"]:
            return {"mode": mode, "status": "needs_human_review" if report["missing_fields"] else "validated_candidate",
                    "candidate": deepcopy(candidate), "attempts": history,
                    "missing_fields": list(report["missing_fields"])}
        request = {"source": source, "failed_candidate": deepcopy(candidate), "validation_errors": deepcopy(report["errors"])}
    return {"mode": mode, "status": "validation_failed", "attempts": history,
            "message": "Correction limit reached; preserve errors for review."}
