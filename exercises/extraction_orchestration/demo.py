"""Default authored protocol responses, real local read-only order enrichment."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from shop_assistant.business import ShopService
from ..extraction.fixtures import SOURCE, CANDIDATE
from ..extraction_reconciliation.fixtures import SCENARIOS
from ..extraction_reconciliation.reconciliation import reconcile
from ..extraction_messages.adapter import ExtractionFailure
from ..extraction_messages.transport import Transport
from .workflow import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["receipt", "reconciliation", "conflict", "correction", "enrichment-failure"], default="receipt")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    arithmetic = args.scenario in ("reconciliation", "conflict")
    source = SCENARIOS["mismatch" if args.scenario == "conflict" else "consistent"] if arithmetic else SOURCE
    name = "reconcile_receipt" if arithmetic else "extract_receipt"
    candidate = reconcile(source)["record"] if arithmetic else deepcopy(CANDIDATE)
    responses = [deepcopy(candidate)]
    if args.scenario == "correction":
        responses[0]["total_cents"]["value"] = 1
        responses.append(deepcopy(candidate))
    def authored(payload):
        return {"type": "message", "role": "assistant", "stop_reason": "tool_use",
                "content": [{"type": "tool_use", "id": "authored-selection", "name": name, "input": responses.pop(0)}]}
    with tempfile.TemporaryDirectory(prefix="shop-extraction-") as directory:
        shop = ShopService(Path(directory))
        def enrich(order_id):
            if args.scenario == "enrichment-failure":
                raise RuntimeError("authored enrichment failure")
            return shop.get_order(order_id)
        try:
            result = run(source, os.environ.get("ANTHROPIC_MODEL", "") if args.live else "offline-fixture",
                         Transport.from_environment() if args.live else authored,
                         mode="live_model" if args.live else "authored_fixture_no_model",
                         kind="unknown" if arithmetic else "extract_receipt", enrich=enrich)
        except ExtractionFailure:
            print(json.dumps({"verification": "UNVERIFIED", "status": "configuration_failed"}))
            return 1
        print(json.dumps({"verification": "LIVE_VALIDATED" if args.live and result["status"] in ("validated_candidate", "enriched") else "UNVERIFIED" if args.live else "OFFLINE_ONLY",
                          "status": result["status"], "schema": result.get("schema"),
                          "trace": result["trace"], "business_events": shop.events(), "ledger": shop.ledger()}, indent=2))
        return 0 if result["status"] in ("validated_candidate", "enriched", "needs_human_review") else 1


if __name__ == "__main__":
    raise SystemExit(main())
