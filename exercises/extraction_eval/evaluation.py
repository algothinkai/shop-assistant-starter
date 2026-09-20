"""Deterministic labeled evaluation, never a live-model accuracy claim."""
import math
import random
from collections import defaultdict

FIELDS = ("order_id", "purchase_date", "currency", "total_cents", "customer_name")


def _score(value):
    return type(value) in (int, float) and 0 <= value <= 1 and math.isfinite(value)


def _validate(rows, split, seen, sources):
    if not isinstance(rows, list) or not rows:
        raise ValueError("A nonempty labeled split is required")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "id", "split", "document_type", "source", "gold", "predicted", "confidence", "source_issue"
        }:
            raise ValueError("Invalid labeled row shape")
        if any(not isinstance(row[k], str) or not row[k].strip()
               for k in ("id", "document_type", "source")):
            raise ValueError("Nonempty row identity, type and source are required")
        if row["split"] != split or row["id"] in seen:
            raise ValueError("Splits must be explicit, unique and disjoint")
        fingerprint = " ".join(row["source"].split())
        if fingerprint in sources:
            raise ValueError("Source documents must be unique within and across splits")
        sources.add(fingerprint)
        seen.add(row["id"])
        if row["source_issue"] not in (None, "ambiguous", "contradictory"):
            raise ValueError("Unknown source issue")
        for key in ("gold", "predicted", "confidence"):
            if not isinstance(row[key], dict) or set(row[key]) != set(FIELDS):
                raise ValueError("Every field requires a label, prediction and score")
        for field in FIELDS:
            for key in ("gold", "predicted"):
                value = row[key][field]
                kind = int if field == "total_cents" else str
                if value is not None and type(value) is not kind:
                    raise ValueError("Invalid field value type")
            if not _score(row["confidence"][field]):
                raise ValueError("Confidence must be a finite number from zero to one")


def _correct(row, field):
    return row["gold"][field] == row["predicted"][field]


def _metrics(pairs):
    count = len(pairs)
    correct = sum(_correct(row, field) for row, field in pairs)
    return {"correct": correct, "count": count, "accuracy": correct / count}


def _band(score):
    return "high" if score >= .9 else "other"


def evaluate(calibration, evaluation, *, target_accuracy=0.9, min_support=2,
             sample_per_stratum=1, seed=7):
    """Select empirical thresholds on calibration; measure only held-out rows."""
    if (not _score(target_accuracy) or type(min_support) is not int or min_support < 1
            or type(sample_per_stratum) is not int or sample_per_stratum < 1
            or type(seed) is not int):
        raise ValueError("Invalid evaluation policy")
    seen = set()
    sources = set()
    _validate(calibration, "calibration", seen, sources)
    _validate(evaluation, "evaluation", seen, sources)
    thresholds = {}
    for kind in sorted({r["document_type"] for r in calibration}):
        thresholds[kind] = {}
        for field in FIELDS:
            rows = [r for r in calibration if r["document_type"] == kind
                    and r["predicted"][field] is not None and r["source_issue"] is None]
            threshold = None
            for candidate in sorted({r["confidence"][field] for r in rows}):
                accepted = [r for r in rows if r["confidence"][field] >= candidate]
                if (len(accepted) >= min_support
                        and sum(_correct(r, field) for r in accepted) / len(accepted) >= target_accuracy):
                    threshold = candidate
                    break
            thresholds[kind][field] = threshold
    segments = {}
    confidence_bins = {}
    for kind in sorted({r["document_type"] for r in evaluation}):
        rows = [r for r in evaluation if r["document_type"] == kind]
        segments[kind] = {}
        confidence_bins[kind] = {}
        for field in FIELDS:
            segments[kind][field] = _metrics([(r, field) for r in rows])
            bins = {}
            for band in ("other", "high"):
                subset = [r for r in rows if _band(r["confidence"][field]) == band]
                if subset:
                    bins[band] = {**_metrics([(r, field) for r in subset]),
                                  "mean_confidence": sum(r["confidence"][field] for r in subset) / len(subset)}
            confidence_bins[kind][field] = bins
    routing = []
    groups = defaultdict(list)
    for row in evaluation:
        reasons = []
        if row["source_issue"]:
            reasons.append("source:" + row["source_issue"])
        for field in FIELDS:
            threshold = thresholds.get(row["document_type"], {}).get(field)
            if row["predicted"][field] is None:
                reasons.append("missing:" + field)
            if threshold is None:
                reasons.append("uncalibrated:" + field)
            elif row["confidence"][field] < threshold:
                reasons.append("low_confidence:" + field)
        priority = (0 if row["source_issue"] else
                    1 if any(r.startswith("missing:") for r in reasons) else 2)
        routing.append({"id": row["id"], "decision": "human_review" if reasons else "candidate_for_reduced_review",
                        "reasons": reasons, "priority": priority if reasons else None})
        groups[(row["document_type"], _band(min(row["confidence"].values())))].append(row["id"])
    rng = random.Random(seed)
    samples = []
    for (kind, band), ids in sorted(groups.items()):
        for ident in sorted(rng.sample(sorted(ids), min(sample_per_stratum, len(ids)))):
            samples.append({"id": ident, "document_type": kind, "confidence_band": band})
    return {"policy": {"target_accuracy": target_accuracy, "min_support": min_support,
                       "sample_per_stratum": sample_per_stratum, "seed": seed},
            "overall": _metrics([(r, f) for r in evaluation for f in FIELDS]),
            "segments": segments, "confidence_bins": confidence_bins, "thresholds": thresholds,
            "routing": routing,
            "review_queue": [r["id"] for r in sorted((r for r in routing if r["reasons"]),
                                                     key=lambda r: (r["priority"], r["id"]))],
            "audit_sample": samples}
