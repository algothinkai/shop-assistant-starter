"""Authored receipt candidates/results, never live model predictions."""

from copy import deepcopy
from pathlib import Path
import json
from exercises.extraction.fixtures import CANDIDATE

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = [
    {"id": "receipt-1003", "source": (ROOT / "receipts/R-1003.txt").read_text()},
    {"id": "receipt-1001", "source": (ROOT / "receipts/R-1001.txt").read_text()},
]
CANDIDATES = {
    "receipt-1003": deepcopy(CANDIDATE),
    "receipt-1001": {
        "order_id": {"value": "O-1001", "evidence": "Order: O-1001"},
        "purchase_date": {"value": "2026-07-03", "evidence": "Date: 2026-07-03"},
        "currency": {"value": "USD", "evidence": "Total: USD 42.00"},
        "total_cents": {"value": 4200, "evidence": "Total: USD 42.00"},
        "customer_name": {"value": "Maya Chen", "evidence": "Customer: Maya Chen"},
    },
}


def succeeded(cid, candidate=None):
    return {
        "custom_id": cid,
        "result": {
            "type": "succeeded",
            "message": {
                "type": "message",
                "role": "assistant",
                "stop_reason": "tool_use",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "extract-" + cid,
                        "name": "extract_receipt",
                        "input": deepcopy(
                            CANDIDATES[cid] if candidate is None else candidate
                        ),
                    }
                ],
            },
        },
    }


def failure(cid, kind="errored", error_type="api_error"):
    result = {"type": kind}
    if kind == "errored":
        result["error"] = {
            "type": "error",
            "error": {
                "type": error_type,
                "message": "Fictional provider failure, not a live response",
            },
        }
    return {"custom_id": cid, "result": result}


def lines(records):
    return "\n".join(json.dumps(r) for r in records) + "\n"


DOCUMENTS.append(
    {"id": "receipt-1002", "source": (ROOT / "receipts/R-1002.txt").read_text()}
)
CANDIDATES["receipt-1002"] = {
    "order_id": {"value": "O-1002", "evidence": "Order: O-1002"},
    "purchase_date": {"value": "2026-08-14", "evidence": "Date: 2026-08-14"},
    "currency": {"value": "USD", "evidence": "Total: USD 129.00"},
    "total_cents": {"value": 12900, "evidence": "Total: USD 129.00"},
    "customer_name": {"value": "Eli Moreno", "evidence": "Customer: Eli Moreno"},
}
