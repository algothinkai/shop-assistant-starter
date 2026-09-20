"""Fixed-origin HTTPS, one bounded call, no redirects/retries; key stays local."""

import http.client
import json
import os
import re
import urllib.error
import urllib.request
from exercises.batch.contracts import BatchFailure, parse
from exercises.tool_loop.transport import NoRedirect

BASE = "https://api.anthropic.com/v1/messages/batches"


def batch_id(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"msgbatch_[A-Za-z0-9_-]{1,100}", value
    ):
        raise BatchFailure("invalid_batch_id")
    return value


class Transport:
    mode = "live_http"

    def __init__(self, key):
        if (
            not isinstance(key, str)
            or not key.strip()
            or len(key) > 1024
            or not key.isascii()
            or "\r" in key
            or "\n" in key
        ):
            raise BatchFailure("missing_or_invalid_local_key")
        self._key = key
        self._opener = urllib.request.build_opener(NoRedirect())

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get("ANTHROPIC_API_KEY", ""))

    def call(self, method, suffix="", body=None, *, jsonl=False):
        if method == "POST":
            if suffix or not isinstance(body, dict):
                raise BatchFailure("invalid_request")
        elif method == "GET":
            parts = suffix.split("/")
            if (
                len(parts) not in (2, 3)
                or parts[0] != ""
                or (len(parts) == 3 and parts[2] != "results")
            ):
                raise BatchFailure("invalid_endpoint")
            batch_id(parts[1])
            if body is not None:
                raise BatchFailure("invalid_request")
        else:
            raise BatchFailure("invalid_method")
        try:
            encoded = (
                None if body is None else json.dumps(body, allow_nan=False).encode()
            )
        except (TypeError, ValueError):
            raise BatchFailure("invalid_request") from None
        if encoded and len(encoded) > 500000:
            raise BatchFailure("request_too_large")
        request = urllib.request.Request(
            BASE + suffix,
            data=encoded,
            method=method,
            headers={
                "content-type": "application/json",
                "x-api-key": self._key,
                "anthropic-version": "2023-06-01",
            },
        )
        limit = 2_000_000 if jsonl else 100000
        try:
            with self._opener.open(request, timeout=20) as response:
                raw = response.read(limit + 1)
            if len(raw) > limit:
                raise BatchFailure("response_too_large")
            return raw.decode("utf-8") if jsonl else parse(raw)
        except urllib.error.HTTPError as exc:
            status = exc.code
            exc.close()
            raise BatchFailure("http_" + str(status)) from None
        except http.client.HTTPException:
            raise BatchFailure("http_protocol_failure") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise BatchFailure("network_failure") from None
        except UnicodeError:
            raise BatchFailure("invalid_response_encoding") from None

    def create(self, body):
        return self.call("POST", body=body)

    def retrieve(self, identifier):
        return self.call("GET", "/" + batch_id(identifier))

    def results(self, identifier):
        return self.call("GET", "/" + batch_id(identifier) + "/results", jsonl=True)
