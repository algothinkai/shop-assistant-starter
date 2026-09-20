"""Authored reconstruction example, no model or network call."""

import json
from .fixtures import case
from .merge import reconstruct
from exercises.batch.fixtures import lines


def main():
    manifest, original, chunks, rows = case()
    report = reconstruct(
        manifest, original, chunks, lines(rows), evidence_mode="authored_fixture"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
