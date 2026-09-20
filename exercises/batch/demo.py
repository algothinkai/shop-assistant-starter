"""Local batch lifecycle decisions using authored provider records; no network."""

import argparse
from copy import deepcopy
import json
from .contracts import bind, BatchFailure
from .workflow import schedule, reconcile, scale_up, retry_plan
from .fixtures import DOCUMENTS, CANDIDATES, succeeded, failure, lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario", choices=["sample", "mixed", "chunk", "missing"], default="mixed"
    )
    args = parser.parse_args()
    payload = bind(
        DOCUMENTS, "offline-model", "Keep integer cents and full labeled evidence."
    )
    records = [succeeded(d["id"]) for d in DOCUMENTS]
    result = {
        "schedule": schedule(
            blocking=False,
            local_tool_roundtrip=False,
            deadline_hours=30,
            cadence_hours=4,
            recovery_hours=2,
        )
    }
    if args.scenario == "sample":
        sample = bind(
            DOCUMENTS[:2], "offline-model", payload["manifest"]["prompt_note"]
        )
        bad = deepcopy(CANDIDATES["receipt-1003"])
        bad["total_cents"]["value"] = 76
        result["before"] = scale_up(
            payload,
            sample["manifest"],
            lines([succeeded("receipt-1003", bad), records[1]]),
            evidence_mode="authored_fixture",
        )
        result["after"] = scale_up(
            payload,
            sample["manifest"],
            lines(records[:2]),
            evidence_mode="authored_fixture",
        )
        result["limitation"] = (
            "Authored before/after candidates illustrate the gate; no measured prompt/model improvement."
        )
    elif args.scenario == "mixed":
        records = [
            failure("receipt-1002", "expired"),
            records[0],
            failure("receipt-1001"),
        ]
        result["import"] = reconcile(payload["manifest"], lines(records), "ended")
        result["retry"] = retry_plan(payload["manifest"], lines(records))
    elif args.scenario == "chunk":
        records = [
            failure("receipt-1003", error_type="invalid_request_error"),
            *records[1:],
        ]
        source = DOCUMENTS[0]["source"]
        split = source.index("Total:")
        result["retry"] = retry_plan(
            payload["manifest"],
            lines(records),
            chunks={"receipt-1003": [source[:split], source[split:]]},
        )
    else:
        records = records[:-1]
        result["import"] = reconcile(payload["manifest"], lines(records), "ended")
        try:
            retry_plan(payload["manifest"], lines(records))
        except BatchFailure as exc:
            result["retry_blocked"] = str(exc)
    print(
        json.dumps(
            {
                "verification": "AUTHORED_BATCH_RECORDS_NO_NETWORK",
                "scenario": args.scenario,
                "result": result,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
