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
    raise NotImplementedError("Complete the CI checkpoint before running its stage checks")


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
