# Stage 5 extension — choose a schema, validate, then enrich (draft)

Start codex/stage-5-orchestration-start; reference codex/stage-5-orchestration-reference.
Edit only exercises/extraction_orchestration/workflow.py: build_request and run.
The prior terminal parser now accepts an expected_name parameter; its default is
unchanged. Run scripts/setup-agent; baseline scripts/test passes. Dedicated
scripts/verify-extraction-orchestration starts unfinished.

## Choose, explain, predict

A compact receipt needs identity/date/value evidence. An itemized receipt instead
needs stated/calculated arithmetic and classification. When the type is unknown,
provide the two strict schemas with tool_choice any. When the input contract is
known, force the named extraction first. Predict why auto could return plain text
and why the order lookup must not run before source validation.

No order or refund tool is exposed during extraction. After a valid compact receipt,
a program may call the existing read-only get_order to enrich it. The arithmetic
record has no order ID; do not guess one from its receipt ID. Any requires an offered
tool, not necessarily the correct schema; validation still gates the next step.
The provided assessor rejects compact-schema selection when explicit itemized
charges are present, so choosing fewer fields cannot hide arithmetic conflicts.
This conservative schema-mismatch case needs review, not automatic lookup.
Unknown compact-source lines also require review: only the documented field lines,
known fictional header/footer, Receipt ID and simple unpriced Item metadata are
allowed. A new charge or malformed label cannot disappear because it was unmodeled.

## Practice

Reuse the format prompt and add a separate reconcile_receipt schema/description.
Scope the entire inherited compact layout/evidence instructions and examples to
extract_receipt only. reconcile_receipt has no evidence fields and follows its
own arithmetic/category schema. Request only the named tool when
known; offer both with any when unknown. Keep disable_parallel_tool_use true.
Use the completed parse/assess helpers to validate protocol and source facts.

Implement at most two generation attempts. An invalid candidate receives original
source, failed candidate and specific errors. After the first selection, force that
schema on correction: switching schemas cannot bypass its errors. Source conflicts,
missing information or unsupported layouts immediately need human review. Protocol
or transport failure stops; it does not trigger automatic retries.

Only validated compact data may invoke enrich(order_id). A successful result must
be an order object with the same ID; errors/mismatched IDs remain enrichment_failed.
This is data lookup, not identity verification, authorization or refund approval.
The arithmetic path finishes validated_candidate without lookup. Preserve the
candidate on successful paths and use a safe trace of request/validation/enrichment
phases, never raw error text. Do not infer network dispatch from generator calls.

Run scripts/verify-extraction-orchestration and
.venv-agent/bin/python -m exercises.extraction_orchestration.demo --scenario receipt.
Repeat with reconciliation, conflict, correction and enrichment-failure. Default
model responses are authored, while receipt enrichment calls the real local
ShopService.get_order and records actual business events. Ledger stays empty.
Predict event order and call counts before looking at the trace.

## Transfer and recovery

Change a candidate calculation while leaving the source consistent: correction can
help. Change the source Total itself: retries cannot repair contradictory source
facts, so review must happen without enrichment. An unknown schema chosen incorrectly
must still fail validation or require review, never obtain a shortcut to lookup.

Optional --live uses the prior local Messages transport and sends fictional source,
examples and correction feedback to Anthropic. Up to two max_tokens2048 requests
may be billable; 20 seconds is a socket timeout, not a hard total deadline. Compatible
model/API access is required; see 05-messages-sources.md. No live run is recorded.
Without access, finish offline and retain UNVERIFIED. any/forced model support is
not universal; never silently change to auto under the same verification claim.

Save your patch and restore only workflow.py from this start. Demo state is temporary;
no key is needed by default. Claude Code/Codex help first asks for method/prediction,
then gives one checkpoint-scoped hint; tool-specific live evidence remains separate.
Unread local runs are self-reported, and hints/reveal do not constitute mastery.
Guide v1.0 tasks4.3/4.4 motivate this lab; actual field-confidence and representative
live evaluations remain required later work.
