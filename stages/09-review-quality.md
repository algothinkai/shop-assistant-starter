# Stage 9 — measure review noise before changing routing

Draft, not approved course content. Python 3.12+, standard library only. Start from
`codex/stage-9-calibration-start` in a new checkout; preserve earlier work with a
commit first. The reference is `codex/stage-9-calibration-reference`. The algothink
manifest records exact commits. Do not merge the reference into your starting copy.
The workbench remains unchanged; `scripts/test` must pass before this exercise.

## Context and prediction

A shop developer stops trusting review comments after several false alarms. The
reviewer also misses a real contradiction. Raising the confidence threshold might
hide a real issue while retaining a confidently wrong report. Decide what to measure
before changing the review prompt. Predict how an absent/failed review affects the
result: it is unresolved, not evidence that the candidate is safe.

There are twelve original code/candidate pairs: six development, six held-out.
They cover correctness, comments and security. These are deliberately tiny teaching
examples, **not a representative production benchmark**. The snippets are text;
never execute them. The labels/rationales are author-adjudicated draft examples.
This is candidate classification, not open-ended bug discovery: missing an unknown
bug is outside this measurement. Label correctness still needs curriculum review.

## Checkpoint A — measure before filtering

Edit only `measure` in `exercises/review_quality/workflow.py`. `dataset` is supplied:
it binds exact code, candidate, label, rationale, category and split to a digest.
Do not copy reference code. First write your prediction for d1, d3 and d4, then
inspect their source and adjudications in fixtures.py. Implement:

- True positive: a real issue is reported; false positive: a non-issue is reported.
- False negative: a real issue is skipped; true negative: a non-issue is skipped.
- Missing or failed judgment: unresolved. Show resolved rates alongside this count;
  partial results cannot be presented as complete performance.
- Precision = TP/(TP+FP); recall on resolved = TP/(TP+FN); false-positive rate on
  resolved = FP/(FP+TN). Zero denominator is null, not 0 or 100%.
- Preserve per-category counts and reported confidence bands with sample sizes.
  A band is a descriptive observation on this corpus, not a calibrated probability.
- Reject duplicate IDs, wrong splits, changed source/labels and malformed confidence.

Run the focused check before implementing routing:

```sh
python3 -m unittest exercises.review_quality.checks.QualityChecks.test_counts_rates_and_high_confidence_false_positive -v
```

Expected authored counts: TP2/FP1/FN1/TN2. Precision is 2/3; false-positive rate is
1/3, not 1/3 of all six candidates. The >=0.8 band has one confirmed issue out of
two reports; below0.8 has one out of one. This is too little evidence for a routing
threshold. Explain why a high-confidence-only rule would preserve d3 and lose d1.

Hints: (1) index the chosen split; (2) validate each unique judgment before counting;
(3) append unresolved entries for missing IDs; (4) compute ratios after counts.

## Checkpoint B — intervene without erasing the evidence

Implement `route`. A manually paused category keeps its reported candidates in
`held_for_prompt_revision`; it does not remove them from measurements or declare
them safe. Other reported candidates go to human review regardless of confidence.
Failed/missing judgments need investigation. Nothing is automatically accepted.
A paused category can contain a real issue: inspect d4 in the revised fixture.

```sh
scripts/verify-review-quality
python3 -m exercises.review_quality.demo --pause-comments
python3 -m exercises.review_quality.demo --revised --pause-comments
python3 -m exercises.review_quality.demo --held-out --revised
```

All ten stage checks should pass in the reference. Both revised fixtures have
perfect toy counts **by authorship**, not because a model improved. Do not claim a
prompt experiment passed from these commands. Baseline tests remain ten passing;
the unfinished stage checks are deliberately separate from installation.

Write a concrete revised criterion: report a comment only when a stated behavior
contradicts reachable code behavior; skip requests for extra explanation or style.
Use d3 as a negative example and d4 as a positive example. Contrast this with
"be conservative". Decide when to restore the category after reviewing evidence.

For a real experiment, freeze criteria using development examples, hide labels and
rationales from the independent reviewer, then collect judgments on previously
unseen held-out code/candidates with the same criteria version. Record actual host,
model/version and outputs locally, validate their corpus/split binding and pass
that run to `measure`. Mark provenance `live_unverified`: this function cannot
verify how observations were obtained. Do not pass gold labels in the host context.
The existing host review adapter expects free-form findings, so its output needs
separate human adjudication; do not treat it as this classifier's judgment format.
If held-out examples already influenced the prompt, they are now development data;
create and independently adjudicate a new held-out set before claiming generalization.
No live model invocation, calibrated routing guarantee or CI configuration is
installed by this lab. With no model/credentials, complete offline arithmetic and
record the real experiment as unverified.

## Evidence, transfer and recovery

Record the exact commit, command, counts, unresolved cases, category pause and
confidence-band sample sizes. Local files not actually read by the learning site
remain self-reported; reading/Reveal is not mastery.

Transfer: a paused category later contains a high-impact genuine defect. Explain
why retaining the queue and human escalation matters, and why a global confidence
cutoff cannot replace category-specific criteria. A second data set has many more
non-issues: explain why precision and false-positive rate change differently.

Recovery: commit or copy your work, then restore only this stage's workflow.py from
the bound start commit in a fresh checkout. Rerun the focused check, then the full
stage check. Do not reset unrelated lessons or local credentials.

Claude Code / Codex assistance prompt (both paths): "Ask me to predict the counts
and explain the distinction between precision and false-positive rate. Review only
my current checkpoint function against these acceptance criteria. Offer one hint
before a patch; do not implement the next checkpoint or claim model quality from
fixtures." This prompt does not certify either host's live behavior.

Source: founder-supplied Claude Certified Architect–Foundations Exam Guide v1.0,
tasks4.1 and4.6. This arithmetic lab adds no API/SDK behavior or changing host flags.
