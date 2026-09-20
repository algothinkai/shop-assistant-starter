"""Local opt-in HTTPS only, bounded bytes, no redirects or automatic retries."""
import http.client
import json
import os
import urllib.error
import urllib.request
from ..tool_loop.transport import NoRedirect
from .adapter import ExtractionFailure


class Transport:
    def __init__(self, key):
        if not isinstance(key, str) or not key.strip() or "\n" in key or "\r" in key:
            raise ExtractionFailure("missing_or_invalid_local_key")
        self._key = key
        self._opener = urllib.request.build_opener(NoRedirect())

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get("ANTHROPIC_API_KEY", ""))

    def __call__(self, payload):
        try:
            body = json.dumps(payload, allow_nan=False).encode()
        except (ValueError, TypeError):
            raise ExtractionFailure("invalid_request") from None
        if len(body) > 60000:
            raise ExtractionFailure("request_too_large")
        request = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"content-type": "application/json", "x-api-key": self._key,
                     "anthropic-version": "2023-06-01"}, method="POST")
        try:
            with self._opener.open(request, timeout=20) as response:
                raw = response.read(100001)
            if len(raw) > 100000:
                raise ExtractionFailure("response_too_large")
            return json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            raise ExtractionFailure(f"http_{code}") from None
        except http.client.HTTPException:
            raise ExtractionFailure("http_protocol_failure") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ExtractionFailure("network_failure") from None
        except (ValueError, UnicodeError):
            raise ExtractionFailure("invalid_response") from None
