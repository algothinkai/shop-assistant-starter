"""Implement request construction and response interpretation for this checkpoint."""
from copy import deepcopy
from ..extraction.schema import SCHEMA


class ExtractionFailure(Exception):
    """Safe static diagnostic; no untrusted response or credentials."""


def build_request(model, request):
    raise NotImplementedError("Build the bounded strict extraction request")


def read_candidate(response):
    raise NotImplementedError("Validate terminal tool response before using its input")


class Generator:
    def __init__(self, model, send):
        self.model, self.send = model, send
        self.calls = 0

    def __call__(self, request):
        payload = build_request(self.model, request)
        self.calls += 1
        return read_candidate(self.send(payload))
