"""Source-bound review aggregation; observations are not correctness certification."""

from copy import deepcopy
import re
from exercises.batch.contracts import digest


class ReviewFailure(ValueError):
    pass


def snapshot(files):
    if not isinstance(files, dict) or not 1 <= len(files) <= 8:
        raise ReviewFailure("invalid_snapshot")
    for name, text in files.items():
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z0-9_/-]+\.py", name)
            or name.startswith("/")
            or ".." in name.split("/")
            or not isinstance(text, str)
            or not text.strip()
            or len(text) > 20000
        ):
            raise ReviewFailure("invalid_source")
    return digest(files)


def plan(files):
    revision = snapshot(files)
    return {
        "revision": revision,
        "passes": [
            {"id": "local:" + name, "files": [name], "purpose": "local correctness"}
            for name in sorted(files)
        ]
        + [
            {
                "id": "integration",
                "files": sorted(files),
                "purpose": "cross-file data flow and existing tests",
            }
        ],
    }


def short(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 2000


def finding(value, files, allowed):
    fields = {
        "path",
        "symbol",
        "cause",
        "severity",
        "confidence",
        "trigger",
        "impact",
        "evidence",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ReviewFailure("invalid_finding")
    if (
        not isinstance(value["path"], str)
        or value["path"] not in allowed
        or not isinstance(value["severity"], str)
        or value["severity"] not in ("P1", "P2", "P3")
        or type(value["confidence"]) not in (float, int)
        or not 0 <= value["confidence"] <= 1
        or not all(short(value[k]) for k in ("symbol", "cause", "trigger", "impact"))
        or not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value["cause"])
        or not isinstance(value["evidence"], list)
        or not 1 <= len(value["evidence"]) <= 8
    ):
        raise ReviewFailure("invalid_finding")
    primary = False
    for loc in value["evidence"]:
        if not isinstance(loc, dict) or set(loc) != {"path", "line", "quote"}:
            raise ReviewFailure("invalid_location")
        name, line = loc["path"], loc["line"]
        if (
            not isinstance(name, str)
            or name not in allowed
            or type(line) is not int
            or not 1 <= line <= len(files[name].splitlines())
            or loc["quote"] != files[name].splitlines()[line - 1]
            or not short(loc["quote"])
        ):
            raise ReviewFailure("unbound_location")
        primary |= name == value["path"]
    if not primary:
        raise ReviewFailure("missing_primary_evidence")
    return digest([value["path"], value["symbol"], value["cause"]])


def aggregate(files, reports, prior=None):
    expected = plan(files)
    if not isinstance(reports, list) or len(reports) > len(expected["passes"]):
        raise ReviewFailure("invalid_reports")
    allowed = {p["id"]: p["files"] for p in expected["passes"]}
    seen, incomplete, groups = set(), [], {}
    for report in reports:
        if (
            not isinstance(report, dict)
            or set(report) != {"pass_id", "revision", "status", "findings"}
            or not isinstance(report["pass_id"], str)
            or report["pass_id"] not in allowed
            or report["pass_id"] in seen
            or report["revision"] != expected["revision"]
            or not isinstance(report["status"], str)
            or report["status"] not in ("complete", "failed")
            or not isinstance(report["findings"], list)
            or len(report["findings"]) > 40
        ):
            raise ReviewFailure("invalid_pass_report")
        pid = report["pass_id"]
        seen.add(pid)
        if report["status"] == "failed":
            incomplete.append(pid)
        for item in report["findings"]:
            key = finding(item, files, allowed[pid])
            group = groups.setdefault(
                key,
                {
                    "fingerprint": key,
                    "path": item["path"],
                    "symbol": item["symbol"],
                    "cause": item["cause"],
                    "observations": [],
                },
            )
            group["observations"].append(
                {"pass_id": pid, "pass_status": report["status"], **deepcopy(item)}
            )
    old = {}
    if prior is not None:
        if (
            not isinstance(prior, dict)
            or set(prior) != {"revision", "issues"}
            or not isinstance(prior["revision"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", prior["revision"])
            or not isinstance(prior["issues"], list)
            or len(prior["issues"]) > 400
        ):
            raise ReviewFailure("invalid_prior")
        for item in prior["issues"]:
            if (
                not isinstance(item, dict)
                or set(item) != {"fingerprint", "path", "symbol", "cause"}
                or not all(short(item[k]) for k in item)
                or item["fingerprint"]
                != digest([item["path"], item["symbol"], item["cause"]])
                or item["fingerprint"] in old
            ):
                raise ReviewFailure("invalid_prior_issue")
            old[item["fingerprint"]] = deepcopy(item)
    incomplete += sorted(set(allowed) - seen)
    for key, group in groups.items():
        group["rerun_status"] = "still_reported" if key in old else "new"
        group["severity_disagreement"] = (
            len({o["severity"] for o in group["observations"]}) > 1
        )
    return {
        "revision": expected["revision"],
        "status": "incomplete" if incomplete else "completed",
        "incomplete_passes": sorted(incomplete),
        "issues": list(groups.values()),
        "not_reobserved": [v for k, v in old.items() if k not in groups],
        "prior_revision": prior["revision"] if prior else None,
        "limitation": "Locations and pass coverage are checked, not bug truth. Absent prior findings are not proven fixed. Confidence is reviewer-reported.",
    }
