"""Authored provider transport, never a live batch or model result."""

from exercises.batch.fixtures import DOCUMENTS, succeeded, lines

ID = "msgbatch_fixture8"


def metadata(status="in_progress", count=2):
    return {
        "type": "message_batch",
        "id": ID,
        "processing_status": status,
        "request_counts": {
            "processing": count if status != "ended" else 0,
            "succeeded": count if status == "ended" else 0,
            "errored": 0,
            "canceled": 0,
            "expired": 0,
        },
        "results_url": "https://untrusted.example/ignored-results",
    }


class AuthoredTransport:
    mode = "authored_transport"

    def __init__(self):
        self.calls = []

    def create(self, body):
        self.calls.append({"method": "POST", "count": len(body["requests"])})
        return metadata(count=len(body["requests"]))

    def retrieve(self, identifier):
        self.calls.append({"method": "GET", "id": identifier})
        return metadata("ended")

    def results(self, identifier):
        self.calls.append({"method": "GET_RESULTS", "id": identifier})
        return lines([succeeded(d["id"]) for d in reversed(DOCUMENTS[:2])])
