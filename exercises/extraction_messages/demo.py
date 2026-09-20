"""Default authored tool response; --live is an explicit potentially billable call."""
import argparse
from copy import deepcopy
import json
import os
from ..extraction.fixtures import CANDIDATE, SOURCE
from ..extraction.pipeline import extract
from .adapter import ExtractionFailure, Generator
from .transport import Transport


def authored_response(payload):
    return {"type": "message", "role": "assistant", "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "fixture-extract-1",
                         "name": "extract_receipt", "input": deepcopy(CANDIDATE)}]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        model = os.environ.get("ANTHROPIC_MODEL", "") if args.live else "offline-fixture"
        send = Transport.from_environment() if args.live else authored_response
        generator = Generator(model, send)
        result = extract(SOURCE, generator, mode="live_model" if args.live else "authored_fixture_no_model")
    except ExtractionFailure:
        print(json.dumps({"verification": "UNVERIFIED", "status": "configuration_failed",
                          "message": "Set a supported local model and API key; do not upload credentials."}))
        return 1
    passed = result["status"] == "validated_candidate"
    # Do not print untrusted model fields, response text, source or transport diagnostics.
    print(json.dumps({"verification": ("LIVE_CANDIDATE_VALIDATED" if passed else "UNVERIFIED")
                      if args.live else "OFFLINE_ONLY",
                      "mode": result["mode"], "status": result["status"],
                      "requests_sent": generator.calls, "validated_attempts": len(result["attempts"]),
                      "limitation": "Narrow source validation only; no accuracy, confidence calibration or refund approval."}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
