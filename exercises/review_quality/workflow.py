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
    raise NotImplementedError("Complete this checkpoint before running its stage checks")


def route(cases, run, paused_categories):
    raise NotImplementedError("Complete this checkpoint before running its stage checks")
