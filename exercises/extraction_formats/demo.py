"""Default authored transfer candidate; optional explicit local Messages experiment."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from ..extraction.pipeline import extract
from ..extraction_messages.adapter import ExtractionFailure
from ..extraction_messages.transport import Transport
from .adapter import Generator, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    case = json.loads(Path(__file__).with_name("transfer.json").read_text())
    def authored(payload):
        return {"type": "message", "role": "assistant", "stop_reason": "tool_use",
                "content": [{"type": "tool_use", "id": "format-fixture", "name": "extract_receipt", "input": deepcopy(case["candidate"])}]}
    try:
        generator = Generator(os.environ.get("ANTHROPIC_MODEL", "") if args.live else "offline-fixture",
                              Transport.from_environment() if args.live else authored)
        result = extract(case["source"], generator, mode="live_model" if args.live else "authored_fixture_no_model", validator=validate)
    except ExtractionFailure:
        print(json.dumps({"verification": "UNVERIFIED", "status": "configuration_failed"}))
        return 1
    success = result["status"] == "validated_candidate"
    print(json.dumps({"verification": ("LIVE_CANDIDATE_VALIDATED" if success else "UNVERIFIED") if args.live else "OFFLINE_ONLY",
                      "mode": result["mode"], "status": result["status"], "generation_calls": generator.calls,
                      "candidates_checked": len(result["attempts"]),
                      "limitation": "Two supported layouts only; no measured few-shot benefit or model accuracy."}, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
