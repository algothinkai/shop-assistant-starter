"""Explicit local live review or authored-envelope demo; never installs CI."""

import argparse
import json
import os
from pathlib import Path
import shutil
from exercises.batch.contracts import parse, BatchFailure
from exercises.code_review.fixtures import FILES
from exercises.code_review.workflow import ReviewFailure, plan, aggregate
from .adapter import run_pass, execute
from .fixtures import envelope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex"), required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--all-passes", action="store_true")
    parser.add_argument("--executable")
    parser.add_argument(
        "--prior", help="Local prior issue inventory JSON, never credentials"
    )
    args = parser.parse_args()
    try:
        prior = None
        if args.prior:
            with open(args.prior, "rb") as file:
                raw = file.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ReviewFailure("prior_too_large")
            prior = parse(raw)
            aggregate(FILES, [], prior)
        model = (
            os.environ.get("SHOP_REVIEW_MODEL", "") if args.live else "authored-model"
        )
        if not model:
            raise ReviewFailure("UNVERIFIED_missing_explicit_model")
        if args.live:
            key = "ANTHROPIC_API_KEY" if args.host == "claude" else "CODEX_API_KEY"
            if not os.environ.get(key):
                raise ReviewFailure("UNVERIFIED_missing_local_api_key")
            executable = args.executable or shutil.which(args.host)
            if not executable:
                raise ReviewFailure("UNVERIFIED_host_unavailable")
            executable = str(Path(executable).absolute())
            env = {
                k: v
                for k, v in os.environ.items()
                if k in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "CODEX_HOME", key)
            }

            def executor(a, p, d):
                return execute(a, p, d, environment=env)
        else:
            executable = "/authored/" + args.host

            def executor(a, p, d):
                # Empty findings are authored input, never a claim of model correctness.
                return envelope(args.host, [])

        tasks = (
            plan(FILES)["passes"]
            if args.all_passes
            else [p for p in plan(FILES)["passes"] if p["id"] == "local:refund.py"]
        )
        reports = []
        failures = []
        for task in tasks:
            try:
                reports.append(
                    run_pass(
                        args.host,
                        executable,
                        model,
                        FILES,
                        task["id"],
                        prior,
                        executor=executor,
                    )
                )
            except ReviewFailure as exc:
                reports.append(
                    {
                        "pass_id": task["id"],
                        "revision": plan(FILES)["revision"],
                        "status": "failed",
                        "findings": [],
                    }
                )
                failures.append({"pass_id": task["id"], "reason": str(exc)})
        print(
            json.dumps(
                {
                    "evidence": "LIVE_HOST_PROCESS"
                    if args.live
                    else "AUTHORED_HOST_ENVELOPES_NO_MODEL",
                    "host": args.host,
                    "failures": failures,
                    "report": aggregate(FILES, reports, prior),
                },
                indent=2,
            )
        )
        return 2 if failures else 0
    except (ReviewFailure, BatchFailure) as exc:
        print(str(exc))
        return 2
    except OSError:
        print("LOCAL_INPUT_UNAVAILABLE")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
