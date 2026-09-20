"""A green job must not hide missing, failed or stale stage observations."""
import unittest
from .workflow import PLAN, collect
from exercises.code_review.workflow import ReviewFailure


class CIChecks(unittest.TestCase):
    def test_all_required_checks_and_revision_are_retained(self):
        calls = []
        def runner(step):
            calls.append(step)
            return 0
        r = collect("a" * 40, False, runner)
        self.assertEqual(calls, list(PLAN))
        self.assertEqual(r["revision"], "a" * 40)
        self.assertEqual(r["status"], "passed")
        self.assertEqual(r["live_model_review"], "UNVERIFIED")
        self.assertFalse(r["worktree_dirty"])

    def test_nonzero_fails_without_skipping_later_checks(self):
        r = collect("b" * 40, True, lambda step: 1 if step[0] == "review_contracts" else 0)
        self.assertEqual(r["status"], "failed")
        self.assertEqual(len(r["checks"]), 4)
        self.assertEqual(r["checks"][-1]["status"], "passed")
        self.assertTrue(r["worktree_dirty"])

    def test_unavailable_timeout_and_bad_outcome_are_not_success(self):
        for error in (OSError("private value"), ReviewFailure("private value"), ValueError("private value")):
            def runner(step):
                raise error
            r = collect("c" * 40, False, runner)
            self.assertEqual(r["status"], "failed")
            self.assertTrue(all(x["exit_code"] is None for x in r["checks"]))
            self.assertNotIn("private value", str(r))
        self.assertEqual(collect("c" * 40, False, lambda _: False)["status"], "failed")

    def test_invalid_source_binding_rejected_before_execution(self):
        def never(_):
            self.fail("must validate before running")
        for revision, dirty in (("main", False), ("g" * 40, False), ("a" * 40, 0)):
            with self.assertRaises(ValueError): collect(revision, dirty, never)
