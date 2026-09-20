"""Authored extraction candidates exercise validation, not model quality."""
import argparse
import copy
import json
from .fixtures import SOURCE, CANDIDATE, authored_generator
from .pipeline import extract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["valid", "correction", "missing", "conflict", "exhausted"], default="correction")
    args = parser.parse_args()
    source = SOURCE
    candidate = copy.deepcopy(CANDIDATE)
    if args.scenario in ("correction", "exhausted"):
        candidate["total_cents"]["value"] = 1
    if args.scenario == "missing":
        source = source.replace("Customer: Noor Patel\n", "")
        candidate["customer_name"] = {"value": None, "evidence": None}
    if args.scenario == "conflict":
        source += "\nTotal: USD 99.00\n"
    candidates = [candidate, CANDIDATE if args.scenario == "correction" else candidate]
    requests = []
    result = extract(source, authored_generator(candidates, requests), mode="authored_fixture_no_model")
    print(json.dumps({"mode": "authored_fixture_no_model", "result": result, "requests": requests}, indent=2))


if __name__ == "__main__":
    main()
