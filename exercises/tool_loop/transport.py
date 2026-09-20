"""Explicit opt-in local HTTPS adapter; no SDK or automatic retries."""
import json
import http.client
import os
import urllib.error
import urllib.request
from .tools import TOOLS


class TransportFailure(Exception):
    """Safe error code only; never include headers, keys or response bodies."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class MessagesTransport:
    def __init__(self, model, key):
        if not model or not key:
            raise TransportFailure("missing_local_model_or_key")
        self.model, self._key = model, key
        self._opener = urllib.request.build_opener(NoRedirect())

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get("ANTHROPIC_MODEL", ""), os.environ.get("ANTHROPIC_API_KEY", ""))

    def __call__(self, history):
        body = json.dumps({"model": self.model, "max_tokens": 512, "messages": history,
                           "tools": TOOLS, "system": "You are a fictional shop teaching assistant. Use only the read-only order tool when needed. Report missing facts honestly; never claim a refund or real action."}).encode()
        if len(body) > 100_000:
            raise TransportFailure("request_too_large")
        request = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"content-type": "application/json", "x-api-key": self._key,
                     "anthropic-version": "2023-06-01"}, method="POST")
        try:
            with self._opener.open(request, timeout=20) as response:
                raw = response.read(100_001)
            if len(raw) > 100_000:
                raise TransportFailure("response_too_large")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise TransportFailure("invalid_response")
            return value
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            raise TransportFailure(f"http_{code}") from None
        except http.client.HTTPException:
            raise TransportFailure("http_protocol_failure") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise TransportFailure("network_failure") from None
        except (ValueError, UnicodeError):
            raise TransportFailure("invalid_response") from None
