"""Authored review observations, no actual model or CI execution."""

import argparse
import json
from .fixtures import FILES, reports
from .workflow import aggregate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", choices=("complete", "failed", "rerun"), default="complete"
    )
    args = parser.parse_args()
    rows = reports()
    prior = None
    if args.scenario == "failed":
        rows[-1]["status"] = "failed"
    elif args.scenario == "rerun":
        original = aggregate(FILES, rows)
        prior = {
            "revision": original["revision"],
            "issues": [
                {k: issue[k] for k in ("fingerprint", "path", "symbol", "cause")}
                for issue in original["issues"]
            ],
        }
    print(
        json.dumps(
            {
                "evidence": "AUTHORED_REVIEW_NO_MODEL",
                "report": aggregate(FILES, rows, prior),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
