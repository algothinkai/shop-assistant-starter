# Stage 9 — independent, source-bound review

Draft tasks1.6,3.6,4.1,4.6. Start codex/stage-9-review-start, reference
codex/stage-9-review-reference. The baseline scripts/test stays green. No new
install is required for this Python standard-library lab. scripts/verify-code-review
is an explicit unfinished exercise until plan and aggregate are implemented.
Current slice: review contracts and authored observations. Actual noninteractive
host/CI execution, schema flags and live review quality are not yet implemented.

## Predict before reviewing

The fictional refund.py excerpt divides cents by100 before calling a function
whose documented input is integer cents. The existing test covers only zero.
A local pass studies one file; an integration pass follows values between files.
Predict why the zero test misses the nonzero bug and which pass has the strongest
cross-file evidence. These are code excerpts, not an executable payment system.

Choose a fixed sequence for this bounded review: one pass per source, then an
integration pass with all sources and tests. An open-ended legacy-testing task
instead starts by mapping risks and adapts its investigation to new dependencies;
this fixed lab does not establish that adaptive skill. Use an independent review
context with code, requirements and tests, excluding the generator's reasoning.
A fresh instance can reduce shared assumptions but does not guarantee accuracy.

## Explicit review criteria

Report a concrete bug only with a trigger, observable impact and exact source
locations. Include security defects when a demonstrable guard violation exists.
Skip naming, formatting, optional refactors, undocumented style preferences and
claims already disproved by the supplied tests. A comment merits a finding only
when its claimed behavior contradicts the implementation. Confidence is reported
for later calibration, never a replacement for these criteria or proof of truth.

Severity examples: P1 is a reproducible broad bypass of the mandatory simulated
identity guard, allowing all teaching refunds without verification. P2 is a
nonzero-amount units error that records the wrong ledger amount. P3 is a localized
recoverable error message contradicting the actual state, without corrupting it.
Explain the impact; do not infer P1 solely from the word payment in a filename.

Few-shot contrast: dividing7600cents by100 before an integer-cents receiver records
76 instead of7600: report the caller and receiver contract. Renaming total_cents to
amount would be a style preference with no changed behavior: do not report it.
An existing zero-input test is relevant context, but it does not cover nonzero
unit conversion; propose the missing case rather than duplicating the zero test.
These examples teach judgment; they are not measured false-positive rates.

## Implement and inspect evidence

Edit exercises/code_review/workflow.py. plan returns a source hash and required
local/integration passes. aggregate validates source revision, pass identity,
locations, required finding fields and scope. Fingerprint by primary path, symbol
and stable snake_case cause. Preserve every observation and disagreement when the
same anchored cause is reported twice. Different causes remain separate. The model
must use consistent anchors; this is not semantic duplicate detection across renames.

Run scripts/verify-code-review, then:

```sh
python3 -m exercises.code_review.demo --scenario complete
python3 -m exercises.code_review.demo --scenario failed
python3 -m exercises.code_review.demo --scenario rerun
```

Expected: completed with one grouped issue/two observations; incomplete with partial
findings retained; still_reported on rerun rather than another new issue. Completed
means the supplied reports cover the plan, not that a model ran or the code is safe.
A failed or missing pass must never become a clean empty result. A prior issue not
observed this time is not_reobserved, not proven fixed; inspect the new code/tests.
No PR comments are posted. A later adapter must validate actual process exit and
terminal output before constructing these pass reports. No fixture certifies that.

Hints: validate before grouping; preserve failure status even with useful findings;
compare fingerprints against prior issue inventory rather than deleting repeated
observations. Run the scope/line checks before trusting any reported confidence.
Transfer: two passes disagree on severity for the same cause. Preserve both and
route for review; do not average severity or choose the more confident author.

Save your patch before restoring only workflow.py from the start. No local state,
network or ledger changes occur. Claude Code/Codex learner prompt: "Ask for my
prediction and reason. Help only the current review-contract function with one
hint; do not implement the entire course." A manual editor uses the same checks.
Unread local evidence is self-reported; Hint/Reveal is not demonstrated mastery.

Next checkpoints must actually exercise noninteractive host commands, fresh review
contexts, structured schemas, project testing guidance, prior-findings input and
quality calibration. Temporarily disabling an empirically noisy category requires
measured examples and an explicit recorded choice, not arbitrary suppression.
