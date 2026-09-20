"""Original labeled candidates and fictional responses, not recorded model runs.

This small corpus teaches measurement, not representative production quality.
Reference adjudications are visible to the author; hide labels in any live prompt.
"""
from .workflow import dataset

DATA = [
    ("d1", "development", "correctness", "def total(cents):\n    return cents / 100  # caller stores returned cents", "Returned amount uses dollars where caller expects cents.", True, "7600 becomes 76 in a cents ledger."),
    ("d2", "development", "correctness", "def empty(xs):\n    return len(xs) == 0", "Empty lists incorrectly return False.", False, "len([]) is zero, so the function returns True."),
    ("d3", "development", "comments", "# Shipping fee is in cents\nfee_cents = 500", "The comment contradicts the value's units.", False, "The explicit field and comment both specify cents."),
    ("d4", "development", "comments", "# Retry at most twice\nfor attempt in range(5):\n    send()", "The comment contradicts five possible sends.", True, "There are five iterations, not at most two."),
    ("d5", "development", "security", "def refund(verified):\n    if not verified: return 'blocked'\n    return 'teaching refund'", "Unverified requests reach the refund branch.", False, "The early return blocks the branch."),
    ("d6", "development", "security", "def refund(verified):\n    return 'teaching refund'", "The supplied verification prerequisite is ignored.", True, "Both True and False reach the refund result."),
    ("h1", "held_out", "correctness", "def pages(n):\n    return n // 10  # number of pages for up to 10 records each", "A partial page is omitted.", True, "Eleven records need two pages but return one."),
    ("h2", "held_out", "correctness", "def count(xs):\n    return sum(1 for x in xs if x is not None)", "Zero-valued items are omitted from the count.", False, "Zero is not None and is counted."),
    ("h3", "held_out", "comments", "# Preserve original order\nreturn list(items)", "The comment should be flagged for not explaining the algorithm.", False, "No behavior contradicts the claim; verbosity is a style preference."),
    ("h4", "held_out", "comments", "# Keep all ticket IDs\nreturn ids[:2]", "The comment falsely promises all IDs.", True, "An input of three IDs loses the third."),
    ("h5", "held_out", "security", "def policy(path):\n    if path not in ALLOWED: raise ValueError()\n    return read_fixture(path)", "Arbitrary paths bypass the explicit allowlist.", False, "The rejection occurs before the read."),
    ("h6", "held_out", "security", "def local_note(note, log):\n    log.write(API_KEY + note)", "The local key is written into the log.", True, "The key is explicitly concatenated; this snippet must not execute."),
]
CASES = [dict(zip(("id", "split", "category", "source", "candidate", "is_issue", "rationale"), row)) for row in DATA]


def authored(split="development", revised=False):
    # Different authored judgments demonstrate arithmetic, not measured improvement.
    verdicts = (["report", "skip", "skip", "report", "skip", "report"] if revised else
                ["report", "skip", "report", "skip", "skip", "report"])
    return {"corpus": dataset(CASES), "split": split, "provenance": "authored",
            "criteria_version": "specific-v2" if revised else "vague-v1",
            "judgments": [{"id": c["id"], "verdict": v, "confidence": confidence if v == "report" else None}
                for c, v, confidence in zip([c for c in CASES if c["split"] == split], verdicts, [0.6, 0.9, 0.99, 0.7, 0.9, 0.95])]}
