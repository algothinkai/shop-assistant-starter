"""Run named deterministic teaching cases and inspect actual local events."""
import argparse
import json
import tempfile
from pathlib import Path
from shop_assistant.business import ShopService
from .workflow import handle_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["human", "ambiguous", "unverified", "verified", "exception", "foreign"], default="unverified")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="shop-after-sales-") as directory:
        shop = ShopService(Path(directory))
        request = {"intent": "refund", "human_requested": False, "order_candidates": ["O-1003"],
                   "amount_cents": 7600, "reason": "Unwanted kettle", "as_of": "2026-09-15"}
        if args.scenario == "human":
            request = {"human_requested": True}
        if args.scenario == "ambiguous":
            request["order_candidates"] = ["O-1002", "O-1003"]
        if args.scenario in ("verified", "exception", "foreign"):
            shop.set_simulated_identity("C-1003", True)
        if args.scenario == "exception":
            request["as_of"] = "2026-11-15"
        if args.scenario == "foreign":
            shop.set_simulated_identity("C-1002", True)
            request["order_candidates"] = ["O-1002"]
        outcome = handle_case(shop, "T-1003", request)
        print(json.dumps({"mode": "deterministic_local_workflow_no_model", "scenario": args.scenario,
                          "outcome": outcome, "events": shop.events(), "ledger": shop.ledger()}, indent=2))


if __name__ == "__main__":
    main()
