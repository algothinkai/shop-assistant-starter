# Stage 5 extension — examples across layouts (draft)

Start codex/stage-5-formats-start; reference codex/stage-5-formats-reference.
Build on the Messages reference. Edit only exercises/extraction_formats/adapter.py.
Run scripts/setup-agent; initial scripts/test remains green. The dedicated
scripts/verify-extraction-formats is an unfinished exercise until implementation.

## Choose and predict

A few-shot prompt supplies a few source/output examples to clarify the desired
behavior. Read examples.json: labeled amount normalization, one inline row, and
missing customer data. Before reading each reason, predict the candidate and why
borrowing a name or truncating a quote would be wrong. The short reasons explain
choices over alternatives; they are authored teaching notes, not model reasoning.

Predict the new transfer.json receipt: different ID, name and amount. Decide why
examples should teach a transformation without donating their facts to this input.
Three examples cover two explicitly supported layouts, not every receipt format.

## Practice

Implement validate to preserve the original complete source line as evidence. For
the documented inline layout, validate its entire row, convert it internally into
the earlier labeled representation and reuse the prior validator. Before mapping,
reject a candidate's evidence that is not a complete line of the original source.
Never return synthesized evidence to the learner. Preserve cross-line conflicts;
an invalid/unsupported Receipt row needs source_unresolved review, not fabricated
null-as-absence. Calendar validity still applies after format conversion.

Implement build_request using the completed Messages builder, keeping the current
source/failed candidate/errors in its user message. Put the three authored examples
and their reasons in separate example blocks in system context, clearly separated
from current receipt data. Describe both layouts, cents/date normalization, missing
nulls and exact original quotes. Do not change tool schema or weaken strict choice.

Run scripts/verify-extraction-formats and
.venv-agent/bin/python -m exercises.extraction_formats.demo. The default generator
returns an authored transfer candidate, not live extraction. The report must say
OFFLINE_ONLY. Inspect the correction and conflicting-total checks: normalization
must not hide source disagreement. Inputs and returned evidence remain unchanged.

Hints: first distinguish candidate value from its evidence; next map only known
complete source rows; finally verify missing and conflicting facts through the
existing validator. A model can learn from examples, but these tests cannot measure
whether few-shot prompting improves it.

## Transfer, optional live and recovery

Add an extra inline column or invalid date to a local copy. Predict review, then run
the matching checks. A new unsupported format needs explicit validation and evals;
example matching cannot establish a universal parser. Compare prompt variants on
separate held-out documents before claiming model improvement; current transfer
fixtures and any example used for tuning are not an independent live evaluation.

An explicit --live on this demo uses the existing Messages transport and local
ANTHROPIC_MODEL/ANTHROPIC_API_KEY. It sends the fictional transfer receipt plus
three fictional examples; up to two requests of max_tokens2048 may be billable.
See 05-messages.md for compatibility, socket timeout and recovery. No live run has
been recorded. Without access, use the offline path and mark live UNVERIFIED.

Save your patch and restore only adapter.py from the formats start. The controller
now accepts an explicit validator argument; its default retains earlier behavior.
No ledger/state reset is needed. Claude Code/Codex assistance must ask for method
and prediction before giving one bounded hint; neither tool is certified by tests.
Reading/hints/reveal are not mastery; unread local evidence stays self-reported.

Source ledger: Guide v1.0 tasks4.2/4.3. First-party prompting reference checked
2026-09-20: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
recommends relevant varied structured examples and3–5 examples; guide skill asks
2–4. This lab uses3 within both ranges. Claims still require model-specific evals.
