"""Authored chunk proposals, never live extraction results."""

from copy import deepcopy
from exercises.batch.contracts import bind
from exercises.batch.fixtures import DOCUMENTS, CANDIDATES, failure, succeeded, lines
from exercises.batch.workflow import retry_plan


def case(source=None):
    docs = deepcopy(DOCUMENTS[:2])
    if source is not None:
        docs[0]["source"] = source
    parent = docs[0]["id"]
    source = docs[0]["source"]
    cut = source.index("Item:")
    chunks = {parent: [source[:cut], source[cut:]]}
    manifest = bind(docs, "fixture-model", "Preserve exact source facts")["manifest"]
    original = lines(
        [failure(parent, error_type="invalid_request_error"), succeeded(docs[1]["id"])]
    )
    plan = retry_plan(manifest, original, chunks=chunks)
    rows = []
    for child in plan["payload"]["manifest"]["documents"]:
        candidate = {
            field: deepcopy(value)
            if value["evidence"] in child["source"]
            else {"value": None, "evidence": None}
            for field, value in CANDIDATES[parent].items()
        }
        rows.append(succeeded(child["id"], candidate))
    return manifest, original, chunks, rows
