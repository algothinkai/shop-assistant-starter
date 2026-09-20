"""Local case snapshots, not SDK sessions or identity authorization."""
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile

FIELDS = {"order_id", "amount_cents", "status", "delivered_on", "customer_expectation"}


def text(value, limit=500):
    return isinstance(value, str) and 0 < len(value) <= limit and bool(value.strip())


def validate(state):
    if not isinstance(state, dict) or set(state) != {"version", "case_id", "issues"}:
        raise ValueError("Invalid case shape")
    if type(state["version"]) is not int or state["version"] != 1 or not text(state["case_id"], 80):
        raise ValueError("Invalid case version or ID")
    issues = state["issues"]
    if not isinstance(issues, dict) or len(issues) > 20:
        raise ValueError("Invalid issues")
    for issue_id, facts in issues.items():
        if not text(issue_id, 80) or not isinstance(facts, dict) or not set(facts) <= FIELDS:
            raise ValueError("Invalid issue facts")
        for field, observations in facts.items():
            if not isinstance(observations, list) or not 1 <= len(observations) <= 20:
                raise ValueError("Invalid observations")
            for observation in observations:
                if not isinstance(observation, dict) or set(observation) != {"value", "source", "observed_at"}:
                    raise ValueError("Invalid observation")
                value = observation["value"]
                if field == "amount_cents":
                    if type(value) is not int or not 0 <= value <= 100_000_000:
                        raise ValueError("Invalid cents")
                elif not text(value):
                    raise ValueError("Invalid fact")
                if not text(observation["source"], 200):
                    raise ValueError("Missing source")
                try:
                    stamp = datetime.fromisoformat(observation["observed_at"])
                    if stamp.tzinfo is None:
                        raise ValueError()
                except (ValueError, TypeError):
                    raise ValueError("Use an explicit observation timezone") from None
    return deepcopy(state)


def new_case(case_id):
    return validate({"version": 1, "case_id": case_id, "issues": {}})


def versions(value):
    if not isinstance(value, dict) or not value or len(value) > 100:
        raise ValueError("Provide a bounded source-version map")
    if not all(text(k, 200) and text(v, 200) for k, v in value.items()):
        raise ValueError("Invalid source version")
    return dict(value)


def save_snapshot(path, state, source_versions):
    """Atomic replacement for one local writer; not concurrent transaction storage."""
    data = {"case": validate(state), "source_versions": versions(source_versions)}
    serialized = json.dumps(data, ensure_ascii=False).encode("utf-8")
    if len(serialized) > 1_000_000:
        raise ValueError("Case snapshot exceeds the read/write size bound")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix="case-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate snapshot key")
        result[key] = value
    return result


def read_snapshot(path):
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError()
        value = json.loads(raw, object_pairs_hook=unique_object)
        if not isinstance(value, dict) or set(value) != {"case", "source_versions"}:
            raise ValueError()
        return {"case": validate(value["case"]), "source_versions": versions(value["source_versions"])}
    except (OSError, ValueError, TypeError):
        raise ValueError("Invalid or unreadable case snapshot; preserve it for inspection") from None
