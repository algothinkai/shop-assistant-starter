"""Original fictional code and authored review observations; never model output."""

from copy import deepcopy
from .workflow import plan

FILES = {
    "refund.py": "def refund(total_cents):\n    return send_refund(total_cents / 100)\n",
    "payment.py": 'def send_refund(amount_cents):\n    """Teaching ledger accepts integer cents."""\n    return {"amount_cents": amount_cents}\n',
    "test_refund.py": 'def test_zero_refund():\n    assert refund(0)["amount_cents"] == 0\n',
}
ISSUE = {
    "path": "refund.py",
    "symbol": "refund",
    "cause": "refund_unit_mismatch",
    "severity": "P2",
    "confidence": 0.9,
    "trigger": "A nonzero total such as 7600 cents is refunded.",
    "impact": "The ledger receives 76 instead of 7600 cents, recording one hundredth of the amount.",
    "evidence": [
        {"path": "refund.py", "line": 2, "quote": FILES["refund.py"].splitlines()[1]}
    ],
}


def reports():
    result = [
        {
            "pass_id": p["id"],
            "revision": plan(FILES)["revision"],
            "status": "complete",
            "findings": [],
        }
        for p in plan(FILES)["passes"]
    ]
    result[1]["findings"] = [deepcopy(ISSUE)]  # sorted payment,refund,test
    cross = deepcopy(ISSUE)
    cross["evidence"].append(
        {"path": "payment.py", "line": 2, "quote": FILES["payment.py"].splitlines()[1]}
    )
    result[-1]["findings"] = [cross]
    return result
