"""Implement schema selection and validation-gated read-only enrichment."""
from copy import deepcopy
import re
from ..extraction_formats.adapter import build_request as build_receipt_request, validate
from ..extraction_messages.adapter import ExtractionFailure, read_candidate
from ..extraction_reconciliation.schema import SCHEMA as RECONCILIATION_SCHEMA
from ..extraction_reconciliation.reconciliation import validate_candidate

TOOLS = ("extract_receipt", "reconcile_receipt")


def build_request(model, request, *, kind="unknown"):
    if kind not in ("unknown", *TOOLS):
        raise ValueError("Unsupported schema selection")
    payload = build_receipt_request(model, request)
    payload["system"] = "Apply the compact section only to extract_receipt.\n<compact_receipt_only>\n" + payload["system"] + "\n</compact_receipt_only>\nThe compact layout, evidence and example instructions above apply only to extract_receipt. reconcile_receipt has no evidence fields; its arithmetic/category schema is validated against the source separately. For itemized arithmetic receipts, use reconcile_receipt: preserve the original stated Total separately from the item-derived total, use explicit tax/shipping/discount, compare calculated minus stated and flag conflicts. Missing required charges mean unknown calculation, not zero. Use kettle/grinder/filter only for an explicit matching category label; other retains a concrete unlisted label as category_detail, while unclear has null detail. Do not erase contradictions or perform business actions. Select the offered schema that fits the source."
    reconciliation = {"name": "reconcile_receipt", "strict": True,
                      "description": "Propose arithmetic and category fields for an itemized receipt. Keep stated and calculated totals distinct in integer cents. Preserve source conflicts; local checks decide correction or review. This performs no lookup, identity verification or payment.",
                      "input_schema": deepcopy(RECONCILIATION_SCHEMA)}
    tools = payload["tools"] + [reconciliation]
    payload["tools"] = tools if kind == "unknown" else [t for t in tools if t["name"] == kind]
    payload["tool_choice"] = ({"type": "any", "disable_parallel_tool_use": True} if kind == "unknown"
                              else {"type": "tool", "name": kind, "disable_parallel_tool_use": True})
    return payload


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
            if re.fullmatch(r"Item: (Ceramic Pour-Over Set|Burr Grinder|Stainless Kettle) x[1-9][0-9]{0,5}", line):
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
    if mode not in ("authored_fixture_no_model", "live_model") or kind not in ("unknown", *TOOLS):
        raise ValueError("Explicit supported mode and schema selection are required")
    if not isinstance(source, str) or not source.strip() or len(source) > 20000:
        raise ValueError("Use a nonempty receipt of at most 20000 characters")
    trace = []
    selected = kind
    request = {"source": source, "failed_candidate": None, "validation_errors": []}
    def outcome(status, **extra):
        return {"mode": mode, "status": status, "schema": None if selected == "unknown" else selected,
                "trace": deepcopy(trace), **extra}
    for attempt in range(1, 3):
        try:
            payload = build_request(model, request, kind=selected)
            trace.append({"phase": "request", "attempt": attempt, "choice": payload["tool_choice"]["type"]})
            name, candidate = parse(send(payload), TOOLS if selected == "unknown" else (selected,))
        except Exception:
            trace.append({"phase": "generation", "status": "failed"})
            return outcome("generation_failed")
        selected = name
        try:
            status, errors = assess(name, source, candidate)
        except Exception:
            trace.append({"phase": "validation", "status": "failed"})
            return outcome("validation_failed")
        trace.append({"phase": "validation", "status": status, "schema": name})
        if status == "needs_human_review":
            return outcome(status, validation_errors=deepcopy(errors))
        if status == "candidate_errors":
            request = {"source": source, "failed_candidate": deepcopy(candidate), "validation_errors": deepcopy(errors)}
            continue
        if status != "validated_candidate":
            return outcome("validation_failed")
        if name == "extract_receipt" and enrich is not None:
            trace.append({"phase": "enrichment", "status": "started"})
            try:
                order_id = candidate["order_id"]["value"]
                order = enrich(order_id)
                if not isinstance(order, dict) or order.get("id") != order_id or "error" in order:
                    raise ValueError("Invalid enrichment result")
            except Exception:
                trace.append({"phase": "enrichment", "status": "failed"})
                return outcome("enrichment_failed")
            trace.append({"phase": "enrichment", "status": "completed"})
            return outcome("enriched", candidate=deepcopy(candidate), order=deepcopy(order))
        return outcome("validated_candidate", candidate=deepcopy(candidate))
    return outcome("validation_failed")
