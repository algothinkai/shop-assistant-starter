# Stage 6 — exact case facts and recovery (draft)

Start: codex/stage-6-start. Reference: codex/stage-6-reference.
No extra dependency or key. scripts/test remains green; scripts/verify-context is
an explicit unfinished exercise on the start. Edit only exercises/context/workflow.py:
record_fact, trim_order, build_context and recover. Supplied state.py handles the
snapshot format and atomic replacement for one local writer.

## Choose, explain, predict

A customer asks about two orders. A narrative summary says only “a small charge
and a replacement soon.” Predict what is lost: cents, dates, order IDs and exact
expectations. Preserve these in a separate issue-keyed case-facts layer, with source
and observation time. Do not let the latest claim overwrite conflicting evidence.
The same repeated observation is idempotent; different observations remain visible.
These recorded claims are context, not proof of identity or approval to refund.

## Practice

record_fact returns an independent validated state and never mutates its input.
Deduplicate exact observations, not values across different sources. trim_order
keeps id/status/total_cents/delivered_on/shipping if present; require an ID, retain
null/missing facts as such, and preserve a structured error verbatim instead of
hiding it. This narrow field selection is for the current return task, not every
future question. Never trim text in the middle of a date or amount.

build_context returns status, conflicts, system and messages. Put complete case
facts first under CASE FACTS, then conflict locations, then NARRATIVE SUMMARY.
Conflicting distinct values in one issue/field yield needs_review; otherwise ready
means context assembled, not a resolved ticket. Keep the full supplied conversation
unchanged in messages, including tool pairs; copying prevents accidental mutation.
This helper does not validate the entire Messages protocol or dispatch anything.
Reject more than200000 serialized characters rather than silently losing history;
this is a local safety bound, not a token count. Bound the summary to10000 chars.

recover compares the exact stored source-version map with current versions,
including added/removed sources. If identical return ready, case, changed_sources[].
Otherwise return refresh_required, case=None, prior_case and changed_sources;
stale observations are for inspection, not automatic prompt reuse. These checks only
cover the sources the caller tracks. Reread changed sources and explicitly build a
new snapshot; matching hashes do not establish freshness of untracked data.

Run scripts/verify-context. Before each run predict python3 -m exercises.context.demo
--scenario resume (also conflict, stale, corrupt). Demos use an actual local order
read and temporary snapshot; conversation/claims are authored. No model, payment or
SDK session call occurs. corrupt exits1; stale retains old facts but refuses case
reuse. conflict can recover matching storage yet still require source review.

## Evidence, transfer and recovery

Compare exact cents/dates/expectations before and after save/load. Explain why
refreshing a changed policy differs from inventing a new customer promise. The full
history and task facts are separate: replacing prior tool results with a vague
summary would break both fidelity and, potentially, tool-result pairing.

Save your patch and restore only workflow.py from the start; demos leave no state.
For either Claude Code or Codex: “Ask for my prediction first; inspect only this
checkpoint and give one hint. Do not complete the entire exercise or change tests.”
Manual editing is the recovery path if either tool is unavailable; their live paths
remain UNVERIFIED. Reading, hints, Reveal and unread local runs are not mastery.

This is a local case-state slice for Guide5.1, with groundwork for1.7/5.4. Real SDK
resume/fork, named CLI sessions, scratchpads, isolated exploration and coordinator
recovery manifests remain separate required labs. Never call this a verified
Claude session or filesystem rewind. See06-sources.md for the version boundary.
