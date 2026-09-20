"""Implement stated/calculated separation and honest category handling."""
from jsonschema import Draft202012Validator
from .schema import SCHEMA


def reconcile(source):
    raise NotImplementedError("Reconcile the explicit receipt without inventing charges")


def validate_candidate(source, candidate):
    """A proposed structured record must match source-derived facts, not just types."""
    report = reconcile(source)
    errors = []
    if list(Draft202012Validator(SCHEMA).iter_errors(candidate)):
        errors.append("schema")
    else:
        errors.extend(field for field, expected in report["record"].items() if candidate[field] != expected)
    return {"status": "needs_human_review" if report["issues"] else "candidate_errors" if errors else "validated_candidate",
            "candidate_errors": errors, "source_report": report}
