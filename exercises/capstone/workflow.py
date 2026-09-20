"""Validate structure and source binding; do not infer learner mastery."""
import json
import sys
from pathlib import Path


class CapstoneError(ValueError):
    pass


def load_json(path):
    try:
        if path.stat().st_size > 1_000_000:
            raise CapstoneError("oversized JSON")
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise CapstoneError("duplicate JSON key")
                result[key] = value
            return result
        return json.loads(path.read_text(), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(CapstoneError("invalid JSON constant")))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise CapstoneError("unreadable JSON") from None


def inspect(cases, responses):
    raise NotImplementedError("Complete Stage 10 after writing independent responses")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("response", type=Path)
    args = parser.parse_args()
    try:
        cases = load_json(Path(__file__).parent / "cases.json")
        report = inspect(cases, load_json(args.response))
    except CapstoneError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report["all_required_evidence_cited"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
