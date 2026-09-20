"""Local commands for the starter. No credential or network integration."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .business import ShopService
from .web import serve


def verify_stage(number: int) -> int:
    if number == 2:
        print("Stage 2 offline protocol checks; start failures are intentional. "
              "These are not live integration evidence.", flush=True)
        return subprocess.call([sys.executable, "-m", "unittest", "exercises.tool_loop.checks", "-v"])
    if number == 1:
        print("Stage 1 exercise checks: failure is expected before the bounded repair. "
              "See stages/01-collaboration.md; baseline tests remain separate.", flush=True)
        return subprocess.call([sys.executable, "-m", "unittest", "exercises.collaboration.checks", "-v"])
    if number != 0:
        print(
            f"Stage {number}: NOT_READY in this starter version. "
            "Read stages/README.md and use the released stage-specific ref when available."
        )
        return 2
    with tempfile.TemporaryDirectory() as directory:
        shop = ShopService(state_dir=Path(directory))
        result = shop.run_preset("T-1001")
        assert result["status"] == "completed"
        assert any(event["operation"] == "get_order" for event in shop.events("T-1001"))
        blocked = shop.run_preset("T-1003")
        assert blocked["status"] == "blocked"
        assert any(event["kind"] == "error" for event in shop.events("T-1003"))
        assert shop.ledger() == []
    print("Stage 0: PASS — successful read, explicit error, no refund ledger mutation.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fictional local Shop Assistant training project")
    sub = parser.add_subparsers(dest="command", required=True)
    server = sub.add_parser("serve", help="Run the local preset workbench")
    server.add_argument("--port", type=int, default=8765)
    demo = sub.add_parser("demo", help="Run one fixed preset in the terminal")
    demo.add_argument("ticket_id")
    sub.add_parser("reset", help="Clear local teaching state")
    sub.add_parser("test", help="Run baseline unit tests")
    stage = sub.add_parser("verify-stage", help="Verify an explicitly released stage")
    stage.add_argument("number", type=int)
    args = parser.parse_args(argv)

    if args.command == "test":
        return subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if args.command == "verify-stage":
        return verify_stage(args.number)
    if args.command == "reset":
        shop = ShopService()
        shop.reset()
        print("Local teaching state reset. No customer, payment or remote account changed.")
        return 0
    shop = ShopService()
    if args.command == "demo":
        result = shop.run_preset(args.ticket_id)
        print(json.dumps(result, indent=2))
        print(json.dumps(shop.events(args.ticket_id), indent=2))
        return 0
    if args.command == "serve":
        serve(shop, port=args.port)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
