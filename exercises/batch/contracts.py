"""Bounded receipt request bindings, reusing the existing extraction adapter."""

from copy import deepcopy
import hashlib
import json
import re
from exercises.extraction_messages.adapter import build_request
from exercises.context.state import unique_object


class BatchFailure(ValueError):
    """Static diagnostics only; never expose provider errors or credentials."""


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, allow_nan=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def parse(text):
    try:
        return json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (ValueError, TypeError, UnicodeError):
        raise BatchFailure("invalid_json") from None


def request(doc, model, prompt_note):
    params = build_request(
        model,
        {"source": doc["source"], "failed_candidate": None, "validation_errors": []},
    )
    params["system"] += "\nQuality focus: " + prompt_note
    return {"custom_id": doc["id"], "params": params}


def bind(documents, model, prompt_note):
    if (
        not isinstance(documents, list)
        or not 1 <= len(documents) <= 20
        or not isinstance(prompt_note, str)
        or not prompt_note.strip()
        or len(prompt_note) > 1000
    ):
        raise BatchFailure("invalid_local_batch")
    ids = set()
    docs = []
    for doc in documents:
        if (
            not isinstance(doc, dict)
            or set(doc) != {"id", "source"}
            or not isinstance(doc["id"], str)
            or not re.fullmatch(r"[a-zA-Z0-9_-]{1,32}", doc["id"])
            or doc["id"] in ids
            or not isinstance(doc["source"], str)
            or not doc["source"].strip()
            or len(doc["source"]) > 20000
        ):
            raise BatchFailure("invalid_document")
        ids.add(doc["id"])
        docs.append(deepcopy(doc))
    requests = [request(doc, model, prompt_note) for doc in docs]
    body = {"requests": requests}
    if len(json.dumps(body).encode()) > 500000:
        raise BatchFailure("local_batch_too_large")
    manifest = {
        "version": 1,
        "documents": docs,
        "model": model,
        "prompt_note": prompt_note,
        "body_sha256": digest(body),
    }
    return {"body": body, "manifest": manifest}


def checked(manifest):
    if (
        not isinstance(manifest, dict)
        or set(manifest)
        != {"version", "documents", "model", "prompt_note", "body_sha256"}
        or type(manifest["version"]) is not int
        or manifest["version"] != 1
    ):
        raise BatchFailure("invalid_manifest")
    payload = bind(manifest["documents"], manifest["model"], manifest["prompt_note"])
    if payload["manifest"] != manifest:
        raise BatchFailure("changed_request_binding")
    return payload
