"""Run the authored evaluation experiment; no network or credentials."""
import json
from pathlib import Path
from .evaluation import evaluate


def main():
    dataset = json.loads(Path(__file__).with_name("labeled.json").read_text())
    rows = dataset["rows"]
    report = evaluate([r for r in rows if r["split"] == "calibration"],
                      [r for r in rows if r["split"] == "evaluation"])
    print(json.dumps({"mode": dataset["mode"], "label_version": dataset["label_version"],
                      "limitations": "Tiny authored lab; not model accuracy or a deployment approval.",
                      **report}, indent=2))


if __name__ == "__main__":
    main()
