"""Implement schema selection and validation-gated read-only enrichment."""
from copy import deepcopy
from ..extraction_formats.adapter import build_request as build_receipt_request, validate
from ..extraction_messages.adapter import ExtractionFailure, read_candidate
from ..extraction_reconciliation.schema import SCHEMA as RECONCILIATION_SCHEMA
from ..extraction_reconciliation.reconciliation import validate_candidate

TOOLS = ("extract_receipt", "reconcile_receipt")


def build_request(model, request, *, kind="unknown"):
    raise NotImplementedError("Choose any schema when unknown; force the known extraction first")


def parse(response, allowed):
    if not isinstance(response, dict) or not isinstance(response.get("content"), list):
        raise ExtractionFailure("invalid_response")
    calls = [b for b in response["content"] if isinstance(b, dict) and b.get("type") == "tool_use"]
    if len(calls) != 1 or calls[0].get("name") not in allowed:
        raise ExtractionFailure("unexpected_extraction_tool")
    name = calls[0]["name"]
    return name, read_candidate(response, expected_name=name)


def assess(name, source, candidate):
    if name == "reconcile_receipt":
        result = validate_candidate(source, candidate)
        return result["status"], result["candidate_errors"]
    report = validate(source, candidate)
    if report["missing_fields"] or any(e["kind"] in ("source_unresolved", "source_conflict") for e in report["errors"]):
        return "needs_human_review", report["errors"]
    return ("candidate_errors" if report["errors"] else "validated_candidate"), report["errors"]


def run(source, model, send, *, mode, kind="unknown", enrich=None):
    raise NotImplementedError("Validate before enrichment; source issues require review")
