"""No network or model calls; authored candidate-classification arithmetic only."""
import argparse
import json
from .fixtures import CASES, authored
from .workflow import route


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--held-out", action="store_true")
    parser.add_argument("--revised", action="store_true")
    parser.add_argument("--pause-comments", action="store_true")
    args = parser.parse_args()
    run = authored("held_out" if args.held_out else "development", args.revised)
    print(json.dumps({"mode": "AUTHORED_NO_MODEL_QUALITY_CLAIM", **route(CASES, run, ["comments"] if args.pause_comments else [])}, indent=2))


if __name__ == "__main__":
    main()
