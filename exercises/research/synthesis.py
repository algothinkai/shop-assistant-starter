"""Attribution/coverage boundary for a known fictional corpus, not an AI coordinator."""

from copy import deepcopy
from datetime import date
import json


def text(value, limit=3000):
    return isinstance(value, str) and 0 < len(value) <= limit and bool(value.strip())


def day(value):
    if not isinstance(value, str):
        raise ValueError("Expected an ISO date")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Use YYYY-MM-DD")
    return parsed


def synthesize(topics, as_of, reports, sources):
    cutoff = day(as_of)
    if (
        not isinstance(topics, list)
        or not 1 <= len(topics) <= 10
        or any(not text(t, 80) for t in topics)
        or len(set(topics)) != len(topics)
        or not isinstance(reports, dict)
        or not isinstance(sources, list)
        or len(sources) > 100
    ):
        raise ValueError("Invalid research request")
    catalog = {}
    for source in sources:
        fields = {
            "id",
            "topic",
            "title",
            "kind",
            "location",
            "published_on",
            "observed_on",
            "effective_on",
            "supersedes",
            "claims",
        }
        if not isinstance(source, dict) or set(source) != fields:
            raise ValueError("Invalid source metadata")
        if (
            any(
                not text(source[k])
                for k in ("id", "topic", "title", "kind", "location")
            )
            or source["id"] in catalog
        ):
            raise ValueError("Invalid source identity")
        day(source["effective_on"])
        day(source["observed_on"])
        if source["published_on"] is not None:
            day(source["published_on"])
        claims = source["claims"]
        if not isinstance(claims, dict) or not 1 <= len(claims) <= 10:
            raise ValueError("Invalid source claims")
        for key, claim in claims.items():
            if (
                not text(key, 80)
                or not isinstance(claim, dict)
                or set(claim) != {"value", "quote"}
                or type(claim["value"]) not in (str, int)
                or not text(claim["quote"])
                or (isinstance(claim["value"], str) and not text(claim["value"]))
            ):
                raise ValueError("Invalid source claim")
        catalog[source["id"]] = source
    for source in sources:
        parent = source["supersedes"]
        if parent is not None and (
            not isinstance(parent, str)
            or parent not in catalog
            or catalog[parent]["topic"] != source["topic"]
            or day(catalog[parent]["effective_on"]) >= day(source["effective_on"])
        ):
            raise ValueError("Invalid temporal supersession")
    eligible = {
        s["id"]
        for s in sources
        if day(s["effective_on"]) <= cutoff
        and (s["published_on"] is None or day(s["published_on"]) <= cutoff)
    }
    superseded = set()
    for sid in eligible:
        parent = catalog[sid]["supersedes"]
        while parent is not None:
            superseded.add(parent)
            parent = catalog[parent]["supersedes"]
    active = eligible - superseded
    outcomes = {}
    for topic in topics:
        required = {sid for sid in active if catalog[sid]["topic"] == topic}
        required_claims = {
            (sid, key) for sid in required for key in catalog[sid]["claims"]
        }
        value = {
            "coverage": "gap",
            "claims": [],
            "historical": [],
            "out_of_scope": [],
            "conflicts": [],
            "missing_sources": sorted(required),
            "missing_claims": [
                {"source_id": sid, "key": key} for sid, key in sorted(required_claims)
            ],
            "attempts": [],
            "error": None,
        }
        outcomes[topic] = value
        report = reports.get(topic)
        if report is None:
            continue
        try:
            if not isinstance(report, dict) or set(report) != {
                "topic",
                "status",
                "attempts",
                "findings",
                "error",
            }:
                raise ValueError("Invalid report shape")
            status = report["status"]
            attempts = report["attempts"]
            findings = report["findings"]
            error = report["error"]
            if report["topic"] != topic or status not in ("ok", "empty", "error"):
                raise ValueError("Invalid report identity")
            if not isinstance(attempts, list) or not 1 <= len(attempts) <= 3:
                raise ValueError("Missing attempts")
            for attempt in attempts:
                if (
                    not isinstance(attempt, dict)
                    or set(attempt) != {"query", "outcome"}
                    or not text(attempt["query"], 1000)
                    or attempt["outcome"] not in ("ok", "empty", "error")
                ):
                    raise ValueError("Invalid attempted query")
            if attempts[-1]["outcome"] != status:
                raise ValueError("Contradictory outcome")
            if (
                not isinstance(findings, list)
                or len(findings) > 100
                or (status == "ok" and not findings)
                or (status == "empty" and findings)
            ):
                raise ValueError("Invalid findings")
            if status == "error":
                if (
                    not isinstance(error, dict)
                    or set(error) != {"type", "retryable", "alternatives"}
                    or error["type"]
                    not in (
                        "timeout",
                        "access_denied",
                        "unavailable",
                        "invalid_response",
                    )
                    or type(error["retryable"]) is not bool
                    or not isinstance(error["alternatives"], list)
                    or not 1 <= len(error["alternatives"]) <= 5
                    or any(not text(a, 500) for a in error["alternatives"])
                ):
                    raise ValueError("Invalid structured error")
            elif error is not None:
                raise ValueError("Failure hidden as success")
            current = []
            history = []
            future = []
            seen = set()
            for finding in findings:
                if not isinstance(finding, dict) or set(finding) != {
                    "source_id",
                    "key",
                    "value",
                    "quote",
                }:
                    raise ValueError("Invalid claim link")
                sid = finding["source_id"]
                key = finding["key"]
                if (
                    not isinstance(sid, str)
                    or not isinstance(key, str)
                    or sid not in catalog
                ):
                    raise ValueError("Unknown source")
                source = catalog[sid]
                if source["topic"] != topic or key not in source["claims"]:
                    raise ValueError("Wrong source topic")
                canonical = source["claims"][key]
                if (
                    type(finding["value"]) is not type(canonical["value"])
                    or finding["value"] != canonical["value"]
                    or finding["quote"] != canonical["quote"]
                ):
                    raise ValueError("Unsupported claim or quote")
                if (sid, key) in seen:
                    continue
                seen.add((sid, key))
                enriched = {
                    **deepcopy(finding),
                    **{
                        k: deepcopy(source[k])
                        for k in (
                            "title",
                            "kind",
                            "location",
                            "published_on",
                            "observed_on",
                            "effective_on",
                            "supersedes",
                        )
                    },
                }
                (
                    future
                    if sid not in eligible
                    else history
                    if sid not in active
                    else current
                ).append(enriched)
            missing_claims = [
                {"source_id": sid, "key": key}
                for sid, key in sorted(
                    required_claims - {(c["source_id"], c["key"]) for c in current}
                )
            ]
            missing = sorted({c["source_id"] for c in missing_claims})
            grouped = {}
            for claim in current:
                grouped.setdefault(claim["key"], set()).add(
                    json.dumps(claim["value"], sort_keys=True)
                )
            conflicts = sorted(k for k, v in grouped.items() if len(v) > 1)
            coverage = (
                ("partial_failure" if findings else "unavailable")
                if status == "error"
                else "empty"
                if status == "empty"
                else "contested"
                if conflicts
                else "gap"
                if missing or not current
                else "supported"
            )
            value.update(
                coverage=coverage,
                claims=current,
                historical=history,
                out_of_scope=future,
                missing_sources=missing,
                missing_claims=missing_claims,
                conflicts=conflicts,
                attempts=deepcopy(attempts),
                error=deepcopy(error),
            )
        except (ValueError, TypeError, KeyError):
            value["coverage"] = "invalid_evidence"
            value["error"] = {
                "type": "invalid_response",
                "retryable": False,
                "alternatives": ["Recheck this report against the cited source."],
            }
    return {
        "as_of": as_of,
        "ready": all(v["coverage"] == "supported" for v in outcomes.values()),
        "topics": outcomes,
    }
