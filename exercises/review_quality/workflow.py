"""Measure labeled candidate judgments; never infer correctness from confidence."""

import hashlib
import json
import math


class QualityError(ValueError):
    pass


def dataset(cases):
    """Bind source, candidate, rationale, category, split and Boolean adjudication."""
    if not isinstance(cases, list) or not 1 <= len(cases) <= 200:
        raise QualityError("invalid corpus")
    ids = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id", "split", "category", "source", "candidate", "rationale", "is_issue"
        }:
            raise QualityError("invalid case")
        if any(not isinstance(case[k], str) or not case[k].strip() or len(case[k]) > 8000
               for k in ("id", "category", "source", "candidate", "rationale")):
            raise QualityError("invalid text")
        if case["split"] not in ("development", "held_out") or type(case["is_issue"]) is not bool:
            raise QualityError("invalid adjudication")
        if case["id"] in ids:
            raise QualityError("duplicate case")
        ids.add(case["id"])
    canonical = sorted(cases, key=lambda c: c["id"])
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()


def measure(cases, run):
    """Missing/failed judgments are unresolved, never a correct negative."""
    digest = dataset(cases)
    if not isinstance(run, dict) or set(run) != {
        "corpus", "split", "provenance", "criteria_version", "judgments"
    }:
        raise QualityError("invalid run")
    if run["corpus"] != digest or run["split"] not in ("development", "held_out"):
        raise QualityError("corpus/split mismatch")
    if run["provenance"] not in ("authored", "live_unverified"):
        raise QualityError("invalid provenance")
    if not isinstance(run["criteria_version"], str) or not run["criteria_version"].strip():
        raise QualityError("missing criteria version")
    selected = {c["id"]: c for c in cases if c["split"] == run["split"]}
    if not selected:
        raise QualityError("empty split")
    judgments = run["judgments"]
    if not isinstance(judgments, list) or len(judgments) > len(selected):
        raise QualityError("invalid judgments")
    seen = set()
    rows = []
    for j in judgments:
        if not isinstance(j, dict) or set(j) != {"id", "verdict", "confidence"}:
            raise QualityError("invalid judgment")
        if not isinstance(j["id"], str) or j["id"] not in selected or j["id"] in seen:
            raise QualityError("unknown, wrong split or duplicate judgment")
        seen.add(j["id"])
        if j["verdict"] not in ("report", "skip", "failed"):
            raise QualityError("invalid verdict")
        confidence = j["confidence"]
        if j["verdict"] == "report":
            if (type(confidence) not in (int, float) or not math.isfinite(confidence)
                    or not 0 <= confidence <= 1):
                raise QualityError("invalid confidence")
        elif confidence is not None:
            raise QualityError("confidence belongs to a reported finding")
        c = selected[j["id"]]
        outcome = ("unresolved" if j["verdict"] == "failed" else
                   ("tp" if c["is_issue"] else "fp") if j["verdict"] == "report" else
                   ("fn" if c["is_issue"] else "tn"))
        rows.append({"id": j["id"], "category": c["category"], "outcome": outcome,
                     "confidence": confidence})
    rows.extend({"id": k, "category": c["category"], "outcome": "unresolved", "confidence": None}
                for k, c in selected.items() if k not in seen)
    rows.sort(key=lambda r: r["id"])

    def metrics(items):
        counts = {k: sum(r["outcome"] == k for r in items)
                  for k in ("tp", "fp", "fn", "tn", "unresolved")}
        def ratio(a, b):
            return a / b if b else None
        return {**counts, "precision": ratio(counts["tp"], counts["tp"] + counts["fp"]),
                "recall_on_resolved": ratio(counts["tp"], counts["tp"] + counts["fn"]),
                "false_positive_rate_on_resolved": ratio(counts["fp"], counts["fp"] + counts["tn"])}

    bands = {}
    for name, low, high in (("below_0.8", 0, 0.8), ("at_least_0.8", 0.8, 1.01)):
        reports = [r for r in rows if r["confidence"] is not None and low <= r["confidence"] < high]
        bands[name] = {"reported": len(reports),
                       "confirmed": sum(r["outcome"] == "tp" for r in reports),
                       "observed_precision": metrics(reports)["precision"]}
    return {"corpus": digest, "split": run["split"], "provenance": run["provenance"],
            "criteria_version": run["criteria_version"], "complete": all(r["outcome"] != "unresolved" for r in rows),
            "scope": "LABELED_CANDIDATE_CLASSIFICATION_NOT_OPEN_ENDED_DETECTION",
            "overall": metrics(rows), "categories": {category: metrics([r for r in rows if r["category"] == category])
                for category in sorted({r["category"] for r in rows})}, "confidence_bands": bands, "rows": rows}


def route(cases, run, paused_categories):
    """A category pause retains findings for prompt revision; nothing auto-accepted."""
    report = measure(cases, run)
    categories = {c["category"] for c in cases}
    if (not isinstance(paused_categories, list) or any(not isinstance(x, str) for x in paused_categories)
            or len(set(paused_categories)) != len(paused_categories)
            or not set(paused_categories) <= categories):
        raise QualityError("invalid paused categories")
    routes = []
    for row in report["rows"]:
        if row["outcome"] == "unresolved":
            destination = "rerun_or_investigate"
        elif row["confidence"] is None:
            destination = "retained_not_reported"
        elif row["category"] in paused_categories:
            destination = "held_for_prompt_revision"
        else:
            destination = "human_review"
        routes.append({"id": row["id"], "destination": destination})
    return {"measurement": report, "routes": routes, "auto_accepted": False}
