"""One local POSIX job, durable intent and serialized operations; no credentials."""

from contextlib import contextmanager
from pathlib import Path
import fcntl
import json
import os
import tempfile
from exercises.batch.contracts import BatchFailure, checked, parse

MAX_STATE = 8_000_000


class Store:
    def __init__(self, path):
        self.path = Path(path).resolve()

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_name(self.path.name + ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield self
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def read(self):
        if not self.path.exists():
            return None
        try:
            with self.path.open("rb") as file:
                raw = file.read(MAX_STATE + 1)
            if len(raw) > MAX_STATE:
                raise BatchFailure("state_too_large")
            value = parse(raw)
            if (
                not isinstance(value, dict)
                or set(value)
                != {"version", "mode", "status", "manifest", "provider", "results"}
                or type(value["version"]) is not int
                or value["version"] != 1
                or value["mode"] not in ("authored_transport", "live_http")
                or value["status"]
                not in ("submission_unknown", "submitted", "ended", "collected")
            ):
                raise BatchFailure("invalid_job_state")
            checked(value["manifest"])
            return value
        except OSError:
            raise BatchFailure("state_read_failed") from None

    def write(self, value):
        raw = json.dumps(value, allow_nan=False).encode()
        if len(raw) > MAX_STATE:
            raise BatchFailure("state_too_large")
        fd, name = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(raw)
                file.flush()
                os.fsync(file.fileno())
            os.replace(name, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            raise BatchFailure("state_write_failed") from None
        finally:
            if os.path.exists(name):
                os.unlink(name)
