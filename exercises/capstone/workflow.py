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


def inspect(cases, responses, case_id=None):
    if (not isinstance(cases, dict) or cases.get("kind") != "AUTHORED_FICTIONAL_CAPSTONE"
            or cases.get("guide_version") != "v1.0"
            or not isinstance(cases.get("cases"), list) or len(cases["cases"]) != 6):
        raise CapstoneError("invalid authored cases")
    ids = [c.get("id") for c in cases["cases"]]
    if len(set(ids)) != 6 or not all(isinstance(x, str) for x in ids):
        raise CapstoneError("duplicate or invalid case ID")
    if case_id is not None and case_id not in ids:
        raise CapstoneError("unknown case")
    if not isinstance(responses, list) or (case_id is None and len(responses) != 6) or (case_id is not None and not 1 <= len(responses) <= 6):
        raise CapstoneError("missing responses")
    by_id = {}
    for r in responses:
        if not isinstance(r, dict) or set(r) != {"id", "choice", "reason", "prediction", "evidence", "transfer_choice", "transfer_reason"}:
            raise CapstoneError("invalid response shape")
        if not isinstance(r["id"], str) or r["id"] in by_id or r["id"] not in ids:
            raise CapstoneError("unknown or duplicate response")
        by_id[r["id"]] = r
    selected = cases["cases"] if case_id is None else [c for c in cases["cases"] if c["id"] == case_id]
    if any(c["id"] not in by_id for c in selected):
        raise CapstoneError("missing selected response")
    observations = []
    for c in selected:
        r = by_id[c["id"]]
        if (not isinstance(r["choice"], str) or not isinstance(r["transfer_choice"], str)
                or r["choice"] not in {v["id"] for v in c["choices"]}
                or r["transfer_choice"] not in {v["id"] for v in c["transfer_choices"]}):
            raise CapstoneError("invalid choice")
        for field in ("reason", "prediction", "transfer_reason"):
            if not isinstance(r[field], str) or not 20 <= len(r[field].strip()) <= 2000:
                raise CapstoneError("missing or oversized reasoning")
        if (not isinstance(r["evidence"], list) or any(not isinstance(x, str) for x in r["evidence"])
                or len(r["evidence"]) != len(set(r["evidence"]))
                or not set(r["evidence"]) <= set(c["evidence"]) or not r["evidence"]):
            raise CapstoneError("invalid evidence keys")
        observations.append({"id": c["id"], "choice_recorded": True,
                             "required_evidence_cited": set(c["required_evidence"]) <= set(r["evidence"]),
                             "reason_recorded": True, "prediction_recorded": True,
                             "transfer_recorded": True, "evidence_source": "self_reported",
                             "demonstrated": False})
    return {"status": "STRUCTURE_ONLY", "all_required_evidence_cited": all(x["required_evidence_cited"] for x in observations),
            "mastery": "UNVERIFIED", "live_model": "UNVERIFIED", "cases": observations}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("response", type=Path)
    parser.add_argument("--case", dest="case_id", choices=["C1","C2","C3","C4","C5","C6"])
    args = parser.parse_args()
    try:
        cases = load_json(Path(__file__).parent / "cases.json")
        report = inspect(cases, load_json(args.response), case_id=args.case_id)
    except CapstoneError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report["all_required_evidence_cited"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
