# Stage 5 extension — evaluate before reducing review (draft)

Start: codex/stage-5-evaluation-start. Reference: codex/stage-5-evaluation-reference.
This extension builds on the completed receipt-validator reference. Only
exercises/extraction_eval/evaluation.py is unfinished; scripts/test stays green.
Use Python 3.12+; no optional packages or credentials are needed here.

## Choose, explain, predict

Read labeled.json: eight fictional labeled/inline receipts, explicit gold values,
and **authored** predictions and confidence scores. These are not model outputs.
Gold means an independently specified expected value, not the model's assertion.
Calibration rows select thresholds; evaluation rows measure a separate held-out
sample. Never use evaluation labels to adjust thresholds and still call it held out.

Before running, predict whether 85% overall accuracy can hide a broken amount
field. Compare an inline amount with its receipt: dollars were mistaken for cents.
Explain why a high confidence score is not a probability guarantee. Predict which
segment cannot support reduced review even with scores over 0.9.

## Practice

Implement evaluate in evaluation.py. Validate rows, unique IDs, disjoint splits,
exact five fields/types and finite scores from 0 to 1. Also reject repeated source
documents after whitespace normalization, even with renamed IDs: duplicates can
leak labels across splits or inflate calibration support. This minimal check cannot
detect semantically duplicated documents rewritten with different text. Reject bad datasets; do not
silently omit failed rows. Report exact-match counts and denominators overall and
for each document type/field. Missing gold/prediction values count as correct only
when both are null, but null predictions always require review.

For each calibration document type/field, try its non-null prediction confidence
values as thresholds. Among predictions at or above a candidate, require at least
min_support labels and observed accuracy >= target_accuracy. Choose the lowest
qualifying threshold, or null when none qualifies. This is an illustrative empirical
rule on tiny authored data, not a statistically certified production policy.

On held-out rows, route ambiguous/contradictory sources, missing values, uncalibrated
segments and below-threshold fields to review. Never consult held-out gold to route.
Prioritize source issues first, then missing data, then calibration/score issues;
ties use ID. A qualifying result says candidate_for_reduced_review, not approved
for automation or financial action.

Report held-out confidence bins per document type/field (high >=0.9, other <0.9):
count, observed accuracy and mean reported confidence. For an ongoing audit,
stratify by document type and the minimum field score's band. Randomly sample up
to sample_per_stratum per group with a supplied seed, including high confidence.
Sampling uses only IDs/types/scores, never gold. Sort IDs before seeded selection
so input order does not change the sample. The seed supports replay, not security.

Run scripts/verify-extraction-eval, then python3 -m exercises.extraction_eval.demo.
Inspect the inline amount's segment accuracy, high-score calibration gap, thresholds,
review reasons and the audit sample. Compare with the aggregate before explaining
why you would retain review. Do not report this as real model extraction accuracy.

## Hints, transfer and recovery

First compute counts rather than percentages. Next separate calibration from held-out
measurement. Finally make routing/sampling independent of evaluation labels. Hints
and reference reading do not establish mastery; unread local results are self-reported.

Transfer: a new receipt format has no calibration data. Predict routing, then change
one held-out document_type and inspect the uncalibrated reasons. Next introduce a
source conflict at confidence 0.99: mandatory review must override the score.
A larger real labeled dataset and a separately held-out evaluation are needed before
choosing production thresholds; changing model/version/layout invalidates assumptions.

Save your patch; restore only evaluation.py from the exact stage-start version bound
in the course. No state or ledger is written. Claude Code/Codex assistance must first
ask for your prediction, limit help to this checkpoint, and preserve the tests.
Neither tool path nor live model confidence is verified by this exercise.
