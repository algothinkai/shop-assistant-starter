"""Implement evidence-preserving layout validation and a bounded few-shot request."""
from copy import deepcopy
import json
from pathlib import Path
import re
from ..extraction.validation import validate as validate_labeled
from ..extraction.schema import SCHEMA
from ..extraction_messages.adapter import build_request as build_base, read_candidate
from jsonschema import Draft202012Validator


def validate(source, candidate):
    raise NotImplementedError("Validate both layouts without inventing original evidence")


def build_request(model, request):
    raise NotImplementedError("Add three source/candidate/rationale examples without replacing current input")


class Generator:
    def __init__(self, model, send):
        self.model, self.send = model, send
        self.calls = 0

    def __call__(self, request):
        payload = build_request(self.model, request)
        self.calls += 1
        return read_candidate(self.send(payload))
