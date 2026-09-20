"""Observable foundation checks; unfinished stages are not in this suite."""

import tempfile
import threading
import unittest
from pathlib import Path

from shop_assistant.business import ShopError, ShopService
from shop_assistant.web import render_page


class ShopBaselineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.shop = ShopService(state_dir=Path(self.directory.name))

    def tearDown(self):
        self.directory.cleanup()

    def test_versioned_policy_and_read_only_functions(self):
        older = self.shop.get_policy("returns", "2026-08-30")
        newer = self.shop.get_policy("returns", "2026-09-15")
        self.assertEqual(older["id"], "POL-RETURN-2026-06")
        self.assertEqual(newer["id"], "POL-RETURN-2026-09")
        self.assertEqual(self.shop.get_order("O-1001")["status"], "shipped")
        self.assertIn("FICTIONAL TRAINING RECEIPT", self.shop.read_receipt("O-1001"))
        self.assertEqual(self.shop.ledger(), [])

    def test_refund_is_guarded_and_only_writes_teaching_ledger(self):
        with self.assertRaises(ShopError) as context:
            self.shop.record_refund("O-1003", 7600, "Return request", "2026-09-15")
        self.assertEqual(context.exception.code, "IDENTITY_REQUIRED")
        self.assertEqual(self.shop.ledger(), [])
        self.shop.set_simulated_identity("C-1003", True)
        refund = self.shop.record_refund("O-1003", 7600, "Return request", "2026-09-15")
        self.assertTrue(refund["teaching_ledger_only"])
        self.assertEqual(refund["policy_id"], "POL-RETURN-2026-09")
        self.assertEqual(len(self.shop.ledger()), 1)
        with self.assertRaises(ShopError) as repeated:
            self.shop.record_refund("O-1003", 7600, "Repeat", "2026-09-15")
        self.assertEqual(repeated.exception.code, "ALREADY_RECORDED")
        self.shop.reset()
        self.assertEqual(self.shop.ledger(), [])
        self.assertFalse(self.shop.simulated_identity_verified("C-1003"))
        self.assertEqual(self.shop.events(), [])

    def test_string_false_cannot_verify_identity_or_enable_refund(self):
        with self.assertRaises(ShopError) as invalid:
            self.shop.set_simulated_identity("C-1003", "false")
        self.assertEqual(invalid.exception.code, "INVALID_IDENTITY_STATE")
        self.assertFalse(self.shop.simulated_identity_verified("C-1003"))
        with self.assertRaises(ShopError) as blocked:
            self.shop.record_refund("O-1003", 7600, "Return request", "2026-09-15")
        self.assertEqual(blocked.exception.code, "IDENTITY_REQUIRED")
        self.assertEqual(self.shop.ledger(), [])
        self.assertTrue(any(event["kind"] == "error" and event["detail"]["code"] == "INVALID_IDENTITY_STATE" for event in self.shop.events()))

    def test_second_instance_cannot_use_stale_identity_or_overwrite_state(self):
        other = ShopService(state_dir=Path(self.directory.name))
        self.shop.set_simulated_identity("C-1003", True)
        other.set_simulated_identity("C-1003", False)
        self.assertFalse(self.shop.simulated_identity_verified("C-1003"))
        with self.assertRaises(ShopError) as blocked:
            self.shop.record_refund("O-1003", 7600, "Return request", "2026-09-15")
        self.assertEqual(blocked.exception.code, "IDENTITY_REQUIRED")
        self.assertEqual(ShopService(state_dir=Path(self.directory.name)).ledger(), [])

    def test_reset_recovers_corrupt_local_state(self):
        self.shop.state_path.write_text("{bad json")
        with self.assertRaises(ShopError) as corrupt:
            self.shop.ledger()
        self.assertEqual(corrupt.exception.code, "STATE_INVALID")
        self.shop.reset()
        self.assertEqual(self.shop.ledger(), [])

    def test_policy_exception_and_invalid_amount_do_not_write_ledger(self):
        self.shop.set_simulated_identity("C-1002", True)
        with self.assertRaises(ShopError) as expired:
            self.shop.record_refund("O-1002", 12900, "Late return", "2026-10-20")
        self.assertEqual(expired.exception.code, "POLICY_EXCEPTION")
        with self.assertRaises(ShopError) as amount:
            self.shop.record_refund("O-1002", 12901, "Too much", "2026-09-15")
        self.assertEqual(amount.exception.code, "INVALID_AMOUNT")
        self.assertEqual(self.shop.ledger(), [])

    def test_identity_revocation_cannot_interleave_with_refund_guard(self):
        self.shop.set_simulated_identity("C-1003", True)
        policy_entered = threading.Event()
        release_policy = threading.Event()
        revocation_started = threading.Event()
        revocation_done = threading.Event()
        errors = []
        original_policy = self.shop._policy_for

        def paused_policy(topic, as_of):
            policy_entered.set()
            if not release_policy.wait(2):
                raise AssertionError("Test policy gate timed out")
            return original_policy(topic, as_of)

        def refund():
            try:
                self.shop.record_refund("O-1003", 7600, "Return request", "2026-09-15")
            except Exception as error:
                errors.append(error)

        def revoke():
            revocation_started.set()
            self.shop.set_simulated_identity("C-1003", False)
            revocation_done.set()

        self.shop._policy_for = paused_policy
        refund_thread = threading.Thread(target=refund)
        revoke_thread = threading.Thread(target=revoke)
        refund_thread.start()
        try:
            self.assertTrue(policy_entered.wait(1))
            revoke_thread.start()
            self.assertTrue(revocation_started.wait(1))
            self.assertFalse(revocation_done.wait(0.1), "Revocation crossed an in-flight refund guard")
        finally:
            release_policy.set()
            refund_thread.join(timeout=2)
            if revoke_thread.ident is not None:
                revoke_thread.join(timeout=2)
        self.assertFalse(refund_thread.is_alive())
        self.assertFalse(revoke_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(self.shop.ledger()), 1)
        self.assertFalse(self.shop.simulated_identity_verified("C-1003"))

    def test_preset_outcomes_are_attributed_and_errors_are_visible(self):
        good = self.shop.run_preset("T-1001")
        self.assertEqual(good["status"], "completed")
        events = self.shop.events("T-1001")
        self.assertEqual([event["kind"] for event in events], ["call", "result", "call", "result", "demo_outcome"])
        self.assertTrue(all(event["ticket_id"] == "T-1001" and event["run_id"] == good["run_id"] for event in events))
        blocked = self.shop.run_preset("T-1003")
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("IDENTITY_REQUIRED", blocked["summary"])
        self.assertTrue(any(event["kind"] == "error" for event in self.shop.events("T-1003")))
        self.assertEqual(self.shop.ledger(), [])
        missing = self.shop.run_preset("T-1004")
        self.assertEqual(missing["status"], "blocked")
        self.assertIn("ORDER_NOT_FOUND", missing["summary"])

    def test_ticket_switch_shows_own_unrun_state_and_escapes_fixture_text(self):
        self.shop.run_preset("T-1001")
        self.shop.catalog["tickets"]["T-1002"]["message"] = '<script>alert("x")</script>'
        page = render_page(self.shop, "T-1002", "test-token")
        self.assertIn("Not run", page)
        self.assertNotIn("RUN-0001", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)
        self.assertIn('aria-current="page"', page)
        self.assertIn("Fixed demo; no model call", page)
        self.assertIn("POL-DAMAGE-2026-06", page)
        self.assertIn('href="#case-title"', page)
        self.assertIn('id="case-title" tabindex="-1"', page)
        self.assertIn("Reveal reference observation after predicting", page)
        self.assertNotIn("Read policy text and expected observation", page)

    def test_workbench_shows_only_selected_tickets_latest_run(self):
        first = self.shop.run_preset("T-1003")
        second = self.shop.run_preset("T-1003")
        page = render_page(self.shop, "T-1003", "test-token")
        self.assertIn(second["run_id"], page)
        self.assertNotIn(first["run_id"], page)
        self.assertEqual(len(self.shop.events("T-1003")), 6)


if __name__ == "__main__":
    unittest.main()
