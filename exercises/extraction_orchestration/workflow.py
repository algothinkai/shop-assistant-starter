"""Implement schema selection and validation-gated read-only enrichment."""
from copy import deepcopy
import re
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
    # A compact schema cannot omit arithmetic facts already present in the source.
    itemized = any(line.strip().casefold().startswith(("subtotal:", "tax:", "shipping:", "discount:"))
                   or (line.strip().casefold().startswith("item:") and "@" in line)
                   for line in source.splitlines())
    if name == "extract_receipt" and itemized:
        return "needs_human_review", ["schema_does_not_cover_arithmetic_source"]
    if name == "extract_receipt":
        metadata = {"HARBOR & BEAN — FICTIONAL TRAINING RECEIPT", "This receipt is sample text. No purchase occurred."}
        for raw in source.splitlines():
            line = raw.strip()
            if not line or line in metadata:
                continue
            if line.startswith(("Order:", "Date:", "Total:", "Customer:", "Receipt |")):
                continue  # The completed format validator checks these values/rows.
            if re.fullmatch(r"Receipt: R-[0-9]{4}", line):
                continue
            if re.fullmatch(r"Item: [^@]+ x[1-9][0-9]*", line) and not re.search(r"\b[A-Z]{3}\s+[0-9]", line):
                continue
            return "needs_human_review", ["unsupported_compact_source_line"]
    if name == "reconcile_receipt":
        result = validate_candidate(source, candidate)
        return result["status"], result["source_report"]["issues"] if result["status"] == "needs_human_review" else result["candidate_errors"]
    report = validate(source, candidate)
    if report["missing_fields"] or any(e["kind"] in ("source_unresolved", "source_conflict") for e in report["errors"]):
        return "needs_human_review", report["errors"] + ["missing:" + field for field in report["missing_fields"]]
    return ("candidate_errors" if report["errors"] else "validated_candidate"), report["errors"]


def run(source, model, send, *, mode, kind="unknown", enrich=None):
    raise NotImplementedError("Validate before enrichment; source issues require review")
