"""Explicit Stage 4 exercise checks; never part of fresh-install baseline."""
import json
import tempfile
import unittest
from pathlib import Path
from shop_assistant.business import ShopService, ShopError
from .workflow import handle_case


def request(**overrides):
    return {"intent": "refund", "human_requested": False, "order_candidates": ["O-1003"],
            "amount_cents": 7600, "reason": "Unwanted kettle", "as_of": "2026-09-15", **overrides}


class WorkflowChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.shop = ShopService(Path(self.directory.name))

    def test_explicit_human_request_does_not_investigate_first(self):
        out = handle_case(self.shop, "T-1003", request(human_requested=True))
        self.assertEqual(out["status"], "needs_human_review")
        calls = [e["operation"] for e in self.shop.events() if e["kind"] == "call"]
        self.assertEqual(calls, ["escalate_case"])
        self.assertEqual(out["handoff"]["root_cause"], "EXPLICIT_HUMAN_REQUEST")
        self.assertEqual(out["handoff"]["attempts"], [])
        self.assertEqual(out["handoff"]["customer_id"], "C-1003")
        self.assertEqual(self.shop.ledger(), [])

    def test_explicit_human_needs_no_refund_fields(self):
        out = handle_case(self.shop, "T-1003", {"human_requested": True})
        self.assertEqual(out["status"], "needs_human_review")
        self.assertIsNone(out["handoff"]["requested_amount_cents"])
        self.assertEqual(out["handoff"]["attempts"], [])

    def test_ambiguous_order_requires_identifier_without_mutation(self):
        out = handle_case(self.shop, "T-1003", request(order_candidates=["O-1002", "O-1003"]))
        self.assertEqual(out["status"], "needs_clarification")
        self.assertEqual(out["code"], "AMBIGUOUS_ORDER")
        self.assertEqual(self.shop.events(), [])
        self.assertEqual(self.shop.ledger(), [])

    def test_request_cannot_supply_verified_identity(self):
        out = handle_case(self.shop, "T-1003", request(verified=True))
        self.assertEqual(out["status"], "invalid_request")
        self.assertFalse(self.shop.simulated_identity_verified("C-1003"))
        self.assertEqual(self.shop.events(), [])

    def test_identity_guard_blocks_refund_call_before_dispatch(self):
        out = handle_case(self.shop, "T-1003", request())
        self.assertEqual(out["code"], "IDENTITY_REQUIRED")
        self.assertEqual(out["status"], "blocked")
        self.assertNotIn("record_refund", [e["operation"] for e in self.shop.events()])
        self.assertEqual(self.shop.ledger(), [])

    def test_verified_success_uses_existing_guard_and_duplicate_stays_blocked(self):
        self.shop.set_simulated_identity("C-1003", True)
        out = handle_case(self.shop, "T-1003", request())
        self.assertEqual(out["status"], "teaching_refund_recorded")
        self.assertTrue(out["record"]["teaching_ledger_only"])
        self.assertEqual(out["record"]["policy_id"], "POL-RETURN-2026-09")
        repeated = handle_case(self.shop, "T-1003", request())
        self.assertEqual(repeated["code"], "ALREADY_RECORDED")
        self.assertEqual(len(self.shop.ledger()), 1)

    def test_policy_exception_has_self_contained_handoff(self):
        self.shop.set_simulated_identity("C-1003", True)
        out = handle_case(self.shop, "T-1003", request(as_of="2026-11-15"))
        self.assertEqual(out["status"], "needs_human_review")
        handoff = out["handoff"]
        self.assertEqual(handoff["root_cause"], "POLICY_EXCEPTION")
        self.assertEqual(handoff["requested_amount_cents"], 7600)
        self.assertEqual(handoff["order_id"], "O-1003")
        self.assertEqual(handoff["policy_id"], "POL-RETURN-2026-09")
        self.assertTrue(handoff["recommended_action"])
        self.assertTrue(handoff["attempts"])
        self.assertEqual(handoff["requested_as_of"], "2026-11-15")
        self.assertEqual(handoff["customer_reason"], "Unwanted kettle")
        self.assertEqual(handoff["observed_order"]["delivered_on"], "2026-09-01")
        self.assertEqual(handoff["observed_policy"]["id"], handoff["policy_id"])
        self.assertEqual(json.loads(out["escalation"]["reason"]), handoff)
        self.assertEqual(self.shop.ledger(), [])

    def test_foreign_order_never_refunds_even_when_both_identities_verified(self):
        self.shop.set_simulated_identity("C-1002", True)
        self.shop.set_simulated_identity("C-1003", True)
        out = handle_case(self.shop, "T-1003", request(order_candidates=["O-1002"]))
        self.assertEqual(out["code"], "ORDER_CUSTOMER_MISMATCH")
        self.assertEqual(out["status"], "needs_clarification")
        self.assertEqual(self.shop.ledger(), [])

    def test_missing_order_clarifies_and_unsupported_policy_escalates(self):
        out = handle_case(self.shop, "T-1004", request(order_candidates=["O-4040"]))
        self.assertEqual(out["status"], "needs_clarification")
        out = handle_case(self.shop, "T-1002", request(order_candidates=["O-1002"], amount_cents=12900))
        self.assertEqual(out["handoff"]["root_cause"], "POLICY_REVIEW_REQUIRED")
        self.assertEqual(self.shop.ledger(), [])

    def test_inquiry_does_not_require_a_refund_amount(self):
        query = request(intent="inquiry", order_candidates=["O-1001"], reason="Where is my order?")
        del query["amount_cents"]
        out = handle_case(self.shop, "T-1001", query)
        self.assertEqual(out["status"], "facts_ready")
        self.assertEqual(out["order"]["id"], "O-1001")
        self.assertEqual(self.shop.ledger(), [])

    def test_revocation_after_preflight_is_checked_at_mutation(self):
        self.shop.set_simulated_identity("C-1003", True)
        original = self.shop.simulated_identity_verified
        def revoke(customer):
            result = original(customer)
            self.shop.set_simulated_identity(customer, False)
            return result
        self.shop.simulated_identity_verified = revoke
        out = handle_case(self.shop, "T-1003", request())
        self.assertEqual(out["code"], "IDENTITY_REQUIRED")
        self.assertEqual(self.shop.ledger(), [])

    def test_failed_handoff_is_not_reported_as_received(self):
        def fail(*args):
            raise ShopError("SIMULATED_ESCALATION_FAILURE", "Teaching handoff unavailable.")
        self.shop.escalate_case = fail
        out = handle_case(self.shop, "T-1003", {"human_requested": True})
        self.assertEqual(out["status"], "blocked")
        self.assertNotIn("escalation", out)
        self.assertEqual(self.shop.ledger(), [])

    def test_malformed_requests_fail_before_business_calls(self):
        for change in ({"human_requested": "false"}, {"amount_cents": True},
                       {"order_candidates": "O-1003"}, {"as_of": "2026-02-31"},
                       {"reason": " "}, {"intent": "invent_policy"}, {"amount_cents": -1}):
            with self.subTest(change=change):
                out = handle_case(self.shop, "T-1003", request(**change))
                self.assertEqual(out["status"], "invalid_request")
        self.assertEqual(self.shop.events(), [])


if __name__ == "__main__":
    unittest.main()
