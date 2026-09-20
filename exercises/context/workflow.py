"""Exact observations and local recovery; no inferred authority or SDK state."""
from copy import deepcopy
import json
from .state import validate, versions, read_snapshot, text, FIELDS


def record_fact(state, issue_id, field, value, source, observed_at):
    result = validate(state)
    if not text(issue_id, 80) or not isinstance(field, str) or field not in FIELDS:
        raise ValueError("Invalid issue or field")
    observation = {"value": value, "source": source, "observed_at": observed_at}
    observations = result["issues"].setdefault(issue_id, {}).setdefault(field, [])
    # Validate before equality deduplication: True must not equal an existing 1 cent.
    probe = deepcopy(result)
    probe["issues"][issue_id][field] = [observation]
    validate(probe)
    if observation not in observations:
        observations.append(deepcopy(observation))
    return validate(result)


def trim_order(result):
    if not isinstance(result, dict):
        raise ValueError("Expected an order or structured error")
    if "error" in result:
        if not isinstance(result["error"], dict) or not text(result["error"].get("code")):
            raise ValueError("Malformed structured error")
        return deepcopy(result)
    if not text(result.get("id"), 80):
        raise ValueError("An order result must identify its order")
    return {key: deepcopy(result[key]) for key in
            ("id", "status", "total_cents", "delivered_on", "shipping") if key in result}


def build_context(state, history, summary):
    facts = validate(state)
    if not isinstance(summary, str) or len(summary) > 10000:
        raise ValueError("Use a bounded narrative summary")
    if not isinstance(history, list) or not history or len(history) > 1000:
        raise ValueError("Provide complete bounded message history")
    if any(not isinstance(m, dict) or m.get("role") not in ("user", "assistant")
           or not isinstance(m.get("content"), (str, list)) for m in history):
        raise ValueError("Invalid message shape")
    conflicts = []
    for issue, fields in facts["issues"].items():
        for field, observations in fields.items():
            if len({json.dumps(o["value"], sort_keys=True) for o in observations}) > 1:
                conflicts.append({"issue": issue, "field": field})
    system = ("CASE FACTS (observations, not authorization)\n"
              + json.dumps(facts, ensure_ascii=False, sort_keys=True)
              + "\nCONFLICTS\n" + json.dumps(conflicts, sort_keys=True)
              + "\nNARRATIVE SUMMARY (secondary to source observations)\n" + summary)
    try:
        serialized = json.dumps({"system": system, "messages": history}, allow_nan=False)
    except (TypeError, ValueError):
        raise ValueError("Context must be JSON-serializable") from None
    if len(serialized) > 200000:
        raise ValueError("Context exceeds the local character bound; do not silently truncate")
    return {"status": "needs_review" if conflicts else "ready", "conflicts": conflicts,
            "system": system, "messages": deepcopy(history)}


def recover(path, current_versions):
    current = versions(current_versions)
    stored = read_snapshot(path)
    prior = stored["source_versions"]
    changed = sorted(key for key in set(prior) | set(current)
                     if prior.get(key) != current.get(key))
    if changed:
        return {"status": "refresh_required", "case": None,
                "prior_case": stored["case"], "changed_sources": changed}
    return {"status": "ready", "case": stored["case"], "changed_sources": []}
