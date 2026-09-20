"""Inspect actual local arithmetic from fictional text; no model or ledger."""
import argparse
import json
from .fixtures import SCENARIOS
from .reconciliation import reconcile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="consistent")
    args = parser.parse_args()
    print(json.dumps({"mode": "DETERMINISTIC_LOCAL_NO_MODEL", **reconcile(SCENARIOS[args.scenario])}, indent=2))


if __name__ == "__main__":
    main()
