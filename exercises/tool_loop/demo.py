"""Run explicit fixture or learner-local live mode; no automatic fallback."""
import argparse
import json
import tempfile
from pathlib import Path
from shop_assistant.business import ShopService
from .fixtures import SCENARIOS, SequenceTransport
from .loop import run_loop
from .transport import MessagesTransport, TransportFailure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Send real API requests using local environment; may incur cost")
    parser.add_argument("--scenario", choices=SCENARIOS, default="happy")
    args = parser.parse_args()
    if args.live and args.scenario != "happy":
        parser.error("--scenario selects offline fixtures only; omit it for live mode")
    mode = "live_api" if args.live else "authored_fixture_no_model"
    try:
        send = MessagesTransport.from_environment() if args.live else SequenceTransport(SCENARIOS[args.scenario])
        with tempfile.TemporaryDirectory() as directory:
            shop = ShopService(Path(directory))
            result = run_loop(send, shop, "Inspect fictional order O-1001. What do the order facts show?")
            output = {"mode": mode, "model": send.model if args.live else None,
                      "api_version": "2023-06-01" if args.live else None,
                      "result": result, "local_tool_events": shop.events(), "ledger": shop.ledger()}
            print(json.dumps(output, indent=2))
        return 0 if result["status"] == "ended" else 1
    except NotImplementedError:
        print("Stage 2 is not implemented yet. Follow stages/02-tool-loop.md; baseline remains runnable.")
        return 2
    except TransportFailure as exc:
        print(json.dumps({"mode": mode, "status": "interrupted", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
