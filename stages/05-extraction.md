# Stage 5 — Validate a receipt candidate (draft)

Start codex/stage-5-start; reference codex/stage-5-reference. Edit only
exercises/extraction/validation.py. Use the existing optional environment via
scripts/setup-agent, then scripts/verify-extraction. The start validator raises
NotImplementedError intentionally; baseline tests remain separate and passing.
No model call or SDK agent run is made by this exercise.

## Choose, explain and predict

Read receipts/R-1003.txt. Predict the shape of an order ID, purchase date, currency,
integer cents and customer name. Decide which values should be nullable if absent.
Explain why a required key with nullable value does not require inventing content.
Inspect schema.py: extra fields are forbidden, value types are explicit and every
field carries a source excerpt. The schema alone cannot prove facts are correct.

Compare the authored candidate with a version whose total_cents is 1 but whose
quote still says USD76.00. Predict which passes shape checks and which fails
semantic validation. “JSON is valid” is not “the amount is supported.”

## Practice and inspect

Implement schema checks with the pinned jsonschema library, then semantic checks
for this lab's labeled receipt lines. Every non-null value needs an exact complete source
line from the correct field, a valid calendar date where relevant, and correct
normalization (integer cents). Do not silently change the candidate or source.

Run scripts/verify-extraction. Inspect .venv-agent/bin/python -m
exercises.extraction.demo --scenario correction (enter the command on one line).
Compare requests: the retry retains the original source, failed candidate and
specific field errors. At most two attempts are permitted; exhaustion is failure.
The supplied generator is authored_fixture_no_model. It does not parse a receipt
with AI, and passing it is not an extraction accuracy score.

Hints: separate schema errors from unsupported values; then inspect the evidence
line, not just whether the value occurs somewhere in the document. Existing receipt
labels are the deliberately narrow supported format, not a universal document parser.

## Missing information and changed conditions

Run the missing, conflict and exhausted scenarios. A genuinely absent field is
null and goes to human review without repeatedly requesting impossible data.
A null field whose labeled value is actually present gets correction feedback.
Present but invalid/unsupported labeled values remain unresolved, not absent.
Conflicting source totals go directly to review instead of picking the convenient
quote. A successful candidate is labeled validated_candidate, not an approved
refund or a calibrated high-confidence extraction. This controller changes no ledger.

Transfer: an unfamiliar document layout may contain the answer but this narrow
validator cannot establish it. Broader format handling needs its own source-aware
validation and evals; do not infer absence or invent a value. Arithmetic calculated
versus stated totals, few-shot/model integration, field/document-type evals,
calibration and stratified sampling remain required later Module 5 work.

## Recovery and bounded assistance

Save your patch, then restore only validation.py from the exact stage-start commit.
The demos use immutable receipt text and local in-memory candidates; no workbench
reset or key is needed. Claude Code or Codex may help after asking for your method
and prediction, one hint at a time, limited to the current validator/check. Do not
replace assertions or let an assistant silently solve the later extraction course.
Local reports the website has not read remain self-reported; Hint/Reveal is not
mastery. Guide v1.0 refs4.2–4.4/5.5 motivate the full module, not a coverage claim
for this small validator slice. Founder curriculum approval remains pending.
