"""Run one explicit lifecycle action. Default authored mode makes no network call."""

import argparse
import json
import os
from exercises.batch.contracts import BatchFailure, bind
from exercises.batch.fixtures import DOCUMENTS
from .fixtures import AuthoredTransport
from .lifecycle import submit, refresh, collect
from .store import Store
from .transport import Transport


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("sample", "status", "collect"))
    parser.add_argument("--job", default=".local/batch-sample.json")
    parser.add_argument(
        "--live", action="store_true", help="Explicitly call the paid local-key API"
    )
    args = parser.parse_args()
    try:
        model = os.environ.get("ANTHROPIC_MODEL", "") if args.live else "fixture-model"
        if args.live and not model:
            raise BatchFailure("UNVERIFIED_missing_explicit_model")
        transport = Transport.from_environment() if args.live else AuthoredTransport()
        store = Store(args.job)
        if args.action == "sample":
            value = submit(
                store, bind(DOCUMENTS[:2], model, "Keep source facts exact"), transport
            )
        else:
            value = (refresh if args.action == "status" else collect)(store, transport)
        print(
            json.dumps(
                {
                    "evidence": "LIVE_HTTP_LOCAL"
                    if args.live
                    else "AUTHORED_TRANSPORT_NO_NETWORK",
                    "status": value["status"],
                    "provider_id": value["provider"]["id"],
                    "all_validated": value["results"]["report"]["all_validated"]
                    if value["results"]
                    else None,
                    "calls": None if args.live else transport.calls,
                }
            )
        )
        return 0
    except BatchFailure as exc:
        print(str(exc))
        return 2
    except (OSError, NotImplementedError):
        print("LOCAL_STAGE_NOT_READY_OR_STORAGE_UNAVAILABLE")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
