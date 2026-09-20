"""Explicit stage exercise checks; never part of first-install foundation tests."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest
from unittest.mock import Mock
import urllib.error
from exercises.batch.contracts import BatchFailure, bind
from exercises.batch.fixtures import DOCUMENTS, lines, succeeded
from .fixtures import AuthoredTransport, metadata
from .lifecycle import submit, refresh, collect
from .store import Store
from .transport import Transport, BASE


class LifecycleChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / "job.json")
        self.payload = bind(DOCUMENTS[:2], "fixture-model", "Keep source facts exact")
        self.transport = AuthoredTransport()

    def ended(self):
        submit(self.store, self.payload, self.transport)
        return refresh(self.store, self.transport)

    def test_restart_collect_in_new_process(self):
        submit(self.store, self.payload, self.transport)
        code = """
import sys
from exercises.batch_lifecycle.store import Store
from exercises.batch_lifecycle.fixtures import AuthoredTransport
from exercises.batch_lifecycle.lifecycle import refresh, collect
s=Store(sys.argv[1]);t=AuthoredTransport()
refresh(s,t);v=collect(s,t)
assert v['status']=='collected' and v['results']['report']['all_validated']
assert [c['method'] for c in t.calls]==['GET','GET_RESULTS']
print('RESTART_GET_ONLY_COLLECTED_AUTHORED')
"""
        run = subprocess.run(
            [sys.executable, "-c", code, str(self.store.path)],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("RESTART_GET_ONLY", run.stdout)
        self.assertEqual(self.store.read()["status"], "collected")

    def test_duplicate_submit_and_concurrency(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(
                    lambda _: submit(
                        Store(self.store.path), self.payload, self.transport
                    ),
                    range(2),
                )
            )
        self.assertEqual(results[0], results[1])
        self.assertEqual([c["method"] for c in self.transport.calls], ["POST"])

    def test_timeout_intent_precedes_post_and_no_replay(self):
        def uncertain(body):
            self.assertEqual(self.store.read()["status"], "submission_unknown")
            raise BatchFailure("network_failure")

        self.transport.create = Mock(side_effect=uncertain)
        with self.assertRaisesRegex(BatchFailure, "network_failure"):
            submit(self.store, self.payload, self.transport)
        for operation in (
            lambda: submit(self.store, self.payload, self.transport),
            lambda: refresh(self.store, self.transport),
            lambda: collect(self.store, self.transport),
        ):
            with self.assertRaisesRegex(BatchFailure, "unresolved_submission"):
                operation()
        self.assertEqual(self.transport.create.call_count, 1)

    def test_malformed_create_retains_unknown(self):
        self.transport.create = Mock(return_value=metadata(count=3))
        with self.assertRaises(BatchFailure):
            submit(self.store, self.payload, self.transport)
        self.assertEqual(self.store.read()["status"], "submission_unknown")

    def test_changed_payload_and_mode_refused(self):
        submit(self.store, self.payload, self.transport)
        other = bind(DOCUMENTS[:1], "fixture-model", "Changed")
        with self.assertRaisesRegex(BatchFailure, "job_already_bound"):
            submit(self.store, other, self.transport)
        self.transport.mode = "live_http"
        with self.assertRaisesRegex(BatchFailure, "transport_mode_changed"):
            refresh(self.store, self.transport)
        self.assertEqual(len(self.transport.calls), 1)

    def test_pending_cannot_download(self):
        submit(self.store, self.payload, self.transport)
        with self.assertRaisesRegex(BatchFailure, "batch_not_ended"):
            collect(self.store, self.transport)
        self.assertEqual(len(self.transport.calls), 1)

    def test_wrong_id_counts_and_regression_preserve_state(self):
        self.ended()
        original = self.store.path.read_bytes()
        variants = [metadata(), metadata("ended", 3), metadata("ended")]
        variants[2]["id"] = "msgbatch_other"
        for value in variants:
            self.transport.retrieve = Mock(return_value=value)
            with self.assertRaises(BatchFailure):
                refresh(self.store, self.transport)
            self.assertEqual(self.store.path.read_bytes(), original)

    def test_invalid_results_leave_ended_for_refetch(self):
        self.ended()
        values = [
            lines([succeeded(DOCUMENTS[0]["id"])]),
            lines([succeeded(DOCUMENTS[0]["id"])] * 2),
            "{}\n",
            lines([succeeded("unknown")]),
        ]
        for value in values:
            self.transport.results = Mock(return_value=value)
            with self.assertRaises(BatchFailure):
                collect(self.store, self.transport)
            self.assertEqual(self.store.read()["status"], "ended")

    def test_provider_counts_must_match_records(self):
        value = metadata("ended")
        value["request_counts"].update(succeeded=1, expired=1)
        self.transport.retrieve = Mock(return_value=value)
        self.ended()
        with self.assertRaisesRegex(BatchFailure, "result_counts_mismatch"):
            collect(self.store, self.transport)

    def test_cached_results_revalidate_and_do_not_refetch(self):
        self.ended()
        value = collect(self.store, self.transport)
        calls = deepcopy(self.transport.calls)
        self.assertEqual(collect(self.store, self.transport), value)
        self.assertEqual(refresh(self.store, self.transport), value)
        self.assertEqual(self.transport.calls, calls)
        value["results"]["report"]["all_validated"] = False
        self.store.write(value)
        with self.assertRaisesRegex(BatchFailure, "invalid_cached_results"):
            collect(self.store, self.transport)

    def test_fixed_origin_and_bounded_transport(self):
        transport = Transport("fictional-test-key")
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps(metadata()).encode()
        transport._opener = Mock()
        transport._opener.open.return_value = response
        transport.retrieve("msgbatch_test")
        request = transport._opener.open.call_args.args[0]
        self.assertEqual(request.full_url, BASE + "/msgbatch_test")
        self.assertEqual(transport._opener.open.call_args.kwargs, {"timeout": 20})
        response.read.assert_called_once_with(100001)
        with self.assertRaises(BatchFailure):
            transport.retrieve("../evil")
        response.read.return_value = b"x" * 100001
        with self.assertRaisesRegex(BatchFailure, "response_too_large"):
            transport.retrieve("msgbatch_test")

    def test_http_diagnostic_does_not_echo_body_or_key(self):
        transport = Transport("fictional-test-key")
        transport._opener = Mock()
        transport._opener.open.side_effect = urllib.error.HTTPError(
            BASE, 429, "secret-body", {}, None
        )
        with self.assertRaises(BatchFailure) as caught:
            transport.retrieve("msgbatch_test")
        self.assertEqual(str(caught.exception), "http_429")


if __name__ == "__main__":
    unittest.main()
