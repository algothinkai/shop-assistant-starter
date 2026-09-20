# Stage 5 extension — stated facts, calculations and categories (draft)

Start codex/stage-5-reconciliation-start; reference codex/stage-5-reconciliation-reference.
Edit only exercises/extraction_reconciliation/reconciliation.py: reconcile.
Run scripts/setup-agent, then the dedicated scripts/verify-extraction-reconciliation.
Baseline scripts/test stays green. This is local arithmetic on fictional documents,
not model output or a refund authorization. It writes no ledger or state.

## Choose and predict

Read fixtures.py. Predict the item subtotal (2 ×19.75 +8.00), then add stated tax
and shipping and subtract the explicit discount. Compare that calculation with
Subtotal and Total in the source. Decide why both stated_total_cents and
calculated_total_cents must survive when they disagree. difference_cents means
calculated minus stated; conflict_detected flags contradictory values, not every
possible missing-data problem. A false conflict flag does not imply readiness.

The lab's narrow format requires Item lines and one each of Subtotal, Tax, Shipping,
Discount and Total, all in the same currency. Zero charges must be explicit;
missing charges are unknown, not zero. Other real receipt conventions are outside
this format and need separate validation. No currency conversion or silent rounding.

## Practice and inspect

Implement exact integer-cent calculations, preserving every original source line
in observations. Reject malformed amounts/quantities and unknown lines. Repeated
amount fields require review even if identical; differing repetitions flag conflict.
Do not use stated Subtotal as the calculation base: recompute from item lines.
An available item subtotal must be compared independently, even if a missing
charge prevents computing the final total; keep both issues visible.
A missing/invalid/duplicated charge makes the calculated total null, while a unique
valid stated Total remains visible. Conversely, a missing/repeated stated Total
does not erase an independently calculable total; its difference stays null and
review remains required. Preserve mismatches and report review issues.

For categories use kettle/grinder/filter when the explicit source label matches
case-insensitively. A known but unlisted label uses other plus its original detail;
? or unclear, a bare other label without concrete detail, a missing label, or multiple category labels requires unclear/null
and review. This is an authored classification convention, not semantic inference
from product names. Other retains a concrete unfamiliar fact; unclear lacks one.

Run scripts/verify-extraction-reconciliation and
.venv-agent/bin/python -m exercises.extraction_reconciliation.demo --scenario mismatch.
Repeat with consistent, missing-charge, mixed-currency, other and unclear. Compare
source observations, stated/calculated totals, difference, conflict flag, category
and issues. validate_candidate checks an authored structured proposal against these
source-derived facts; a schema-valid wrong calculation needs correction, but a
conflicting source needs human review. No repeated model attempt can repair source
truth without new evidence. This slice does not call a model or run a correction loop.

Hints: calculate with cents, separate missing from zero, then compare rather than
replace. Explain why a confident proposal cannot reconcile contradictory originals.
Transfer: add an unknown Handling charge or a third category label. Predict review
before running a local check; never discard unfamiliar evidence to make totals fit.

Save your patch; restore only reconciliation.py from this exact start. No state
reset or key is needed. Claude Code/Codex help must first ask for your prediction,
then one bounded hint; using either assistant is optional. Unread local observations
stay self-reported. Reading/reference/reveal is not mastery.

Guide v1.0 tasks4.3/4.4 motivate nullable/category schemas and calculated-versus-stated
fields. Source labels and formulas here are explicit fictional lab conventions.
Actual model extraction, prompt/routing integration and representative evals remain
separate work; no new vendor-interface behavior or full coverage is claimed.
