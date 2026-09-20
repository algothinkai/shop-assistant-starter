# Stage 1 reference — review only after attempting the checkpoint

Start commit: 3d2edf1a40dd7d64d01b4f95c6ce153f1a71fec8.
The repair changes only report.py. Filter by run before counting; use the terminal
outcome instead of guessing from successful calls. The original checks are
unchanged. One pass takes O(n) time and O(1) auxiliary space. This operates on the
ordered, trusted local log; it does not claim to validate arbitrary network input.

Run scripts/verify-stage 1, scripts/test and scripts/verify-stage 0. All should pass.
A passing unit test proves Python behavior, not Claude Code instruction loading,
skill invocation, permission enforcement or a learner's independent reasoning.
No live Claude Code/Codex run was performed for this reference. Inspect the diff
from the start commit and explain a changed-input case before claiming learning.

The supplied scoped rule and skill are configuration examples in the start, not
reference answers. For checkpoint B, diagnose shared versus personal scope and
verify observed loading in your own tool. Current official docs differ from guide
wording as recorded in 01-collaboration.md; retain UNVERIFIED when unsupported.
