"""Run a fixed bounded offline plan, retain failures and bind evidence to Git."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from exercises.code_review.workflow import ReviewFailure
from exercises.review_host.adapter import execute

ROOT = Path(__file__).resolve().parents[2]
PLAN = (
    ("foundation", "unittest", "discover", "-s", "tests", "-v"),
    ("review_contracts", "unittest", "exercises.code_review.checks", "-v"),
    ("host_boundaries", "unittest", "exercises.review_host.checks", "-v"),
    ("quality_measurement", "unittest", "exercises.review_quality.checks", "-v"),
)


def run_check(step):
    # No local provider credentials or user configuration enter the test process.
    env = {"PATH": os.defpath, "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    _, _, code = execute([sys.executable, "-m", *step[1:]], "", ROOT,
                         timeout=120, environment=env)
    return code


def collect(revision, dirty, runner=run_check):
    """A failed check must fail the report while preserving remaining observations."""
    if (not isinstance(revision, str) or len(revision) != 40
            or any(c not in "0123456789abcdef" for c in revision) or type(dirty) is not bool):
        raise ValueError("invalid Git evidence")
    results = []
    for step in PLAN:
        try:
            code = runner(step)
            if type(code) is not int:
                raise ValueError("invalid process outcome")
            results.append({"check": step[0], "status": "passed" if code == 0 else "failed",
                            "exit_code": code, "reason": None if code == 0 else "nonzero_exit"})
        except (ReviewFailure, OSError, ValueError):
            # Do not serialize exception messages, subprocess output or environment.
            results.append({"check": step[0], "status": "failed", "exit_code": None,
                            "reason": "execution_unverified_run_check_locally"})
    return {"schema_version": 1, "revision": revision, "worktree_dirty": dirty,
            "scope": "OFFLINE_TEST_EXECUTION_ONLY", "live_model_review": "UNVERIFIED",
            "status": "passed" if all(r["status"] == "passed" for r in results) else "failed",
            "checks": results}


def main():
    output = ROOT / ".local/ci/review.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    # Remove stale evidence before starting; a killed invocation cannot leave old green output.
    output.unlink(missing_ok=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
    report = collect(revision, dirty)
    payload = json.dumps(report, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, delete=False) as file:
        file.write(payload)
        name = file.name
    os.replace(name, output)
    print(payload, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
