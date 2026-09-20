# Stage 7 — attributed research outcomes (partial draft)

Start codex/stage-7-start; reference codex/stage-7-reference. Python standard
library only. Edit synthesize in exercises/research/synthesis.py. scripts/test
stays green; scripts/verify-research is the explicit unfinished exercise.

## Choose, explain, predict

The shop's September policy says 45 return days; an authored fictional FAQ says 30
for the same period. June's 30-day policy was explicitly superseded. Predict which
comparison is a real current conflict and which is a temporal difference. Never
silently choose the newest, shorter or more convenient value.

This lab reuses actual existing fictional policy text and adds one deliberately
conflicting fictional FAQ. Existing policies record effective dates, not publication
dates: published_on remains null. Observed_on records when this exercise snapshot
was assembled. Research findings do not authorize a refund or verify identity.

## Implement

Inputs are explicit topics, as_of, one final report per topic and a known local
source inventory. This inventory is a bounded teaching corpus, not the entire web.
Preserve exact claim-source links, quote, title/kind/location and dates in output.
Reject unsupported values/quotes or wrong-topic attribution without discarding an
independent sibling report. Duplicated findings must not manufacture extra support.

Within as_of, explicit supersession separates historical claims from current ones;
future-effective or future-published sources go to out_of_scope. Preserve conflicts
among active claims. The known inventory makes missing active sources visible:
return missing_sources and exact missing_claims for a targeted follow-up. Every
active claim in this bounded corpus is required, not merely one mention per source.
This is not a claim of exhaustive external coverage. Supersession replaces a whole
source version; it is not inferred separately for individual clauses.
Source reports carry attempted queries and outcomes; errors retain type, retryable
and alternative actions. An access failure is not an empty successful search.
A report can contain useful partial findings and still have an unresolved error.

Output topics each have coverage, claims, historical, out_of_scope, conflicts,
missing_sources, missing_claims, attempts and error. Coverage is supported, contested, gap, empty,
unavailable, partial_failure or invalid_evidence. Overall ready requires every
requested topic supported; it never means approved policy or completed business
resolution. Metadata dates and null publication dates must survive synthesis.

Run scripts/verify-research then python3 -m exercises.research.demo --scenario conflict.
Repeat historical, gap, empty, failure and partial; predict coverage and preserved
source IDs first. Default reports are authored, not returned by model subagents.
Keep one healthy topic while another fails; propose which exact missing source or
failed query a coordinator should revisit. Do not retry a genuine policy conflict
until it disappears or average 30 and 45 into an invented policy.

## Transfer and recovery

Change the effective date versus publication date and explain their different
roles. Add an unindexed source and explain why known-corpus completeness does not
prove exhaustive external research. A disputed source needs attribution and human
policy review, not a silent rewrite. Save your patch and restore only synthesis.py
from the start. No persistent ledger, key or model is involved.

Both Claude Code/Codex help prompts: “Ask me to predict source status and explain
my choice first; give one hint limited to synthesize. Do not implement later modules.”
Manual editing is the recovery path without tools. Unread local evidence remains
self-reported; Hint/Reveal never demonstrate mastery.

Guide v1.0 tasks 5.3/5.6 motivate this contract. Actual adaptive coordinator decisions,
parallel Agent SDK subagents, scoped tools, explicit prompts, local retries and
gap-driven re-delegation are required next work, not implemented by this fixed demo.
Current SDK docs use Agent where the guide says Task; checked 2026-09-20 at
https://code.claude.com/docs/en/agent-sdk/subagents . Do not silently mix versions
or infer live delegation from an AgentDefinition or a deterministic report.
