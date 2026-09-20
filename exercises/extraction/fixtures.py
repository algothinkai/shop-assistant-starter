"""Authored candidate objects for known fictional receipts; not extracted by AI."""
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "receipts/R-1003.txt").read_text()
CANDIDATE = {
    "order_id": {"value": "O-1003", "evidence": "Order: O-1003"},
    "purchase_date": {"value": "2026-08-28", "evidence": "Date: 2026-08-28"},
    "currency": {"value": "USD", "evidence": "Total: USD 76.00"},
    "total_cents": {"value": 7600, "evidence": "Total: USD 76.00"},
    "customer_name": {"value": "Noor Patel", "evidence": "Customer: Noor Patel"},
}


def authored_generator(candidates, requests):
    remaining = iter(deepcopy(candidates))
    def generate(request):
        requests.append(deepcopy(request))
        return next(remaining)
    return generate
