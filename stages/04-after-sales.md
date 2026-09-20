# Stage 4 — Reliable after-sales workflow (draft)

Start: codex/stage-4-start. Reference: codex/stage-4-reference. Build on Stage 3's
reference without changing the baseline workbench. Edit only
`exercises/after_sales/workflow.py`; checks intentionally fail on the start.
Run `scripts/test` for the passing baseline and `scripts/verify-stage 4` for this
exercise. No optional SDK, model key or network is needed for this local slice.

## 1. Decide before acting

A customer asks for a human. Choose between investigating the order first and
recording a handoff immediately; explain what the customer actually requested.
Predict the call sequence. Implement explicit human-request handling before
order lookup. Check the real events: only escalate_case should be called.

Then try two candidate order IDs. Ask for the identifier instead of choosing the
newest, largest or first order. A customer's frustration alone is not a reason to
invent a preference for human help. This lab takes a structured request; it does
not claim to infer intent or sentiment from free text. The later prompt examples
and live agent exercise must validate that separate interpretation step.

Hint: inspect ticket identity before deciding what order belongs to the case.
Further hint: explicit human preference needs no refund amount or order lookup.
Transfer: no human request, clear order and a routine question. Returning verified
facts may be appropriate; unconditional escalation would avoid the actual task.

## 2. Enforce prerequisites

Predict the ledger and function calls when identity is unverified, when the
selected order belongs to another customer, and when the request contains
verified=true. Implement a workflow preflight, while retaining the existing
atomic record_refund guard. Never let learner request fields set identity.
`set_simulated_identity(customer_id, True)` is an explicit local teaching setup,
not real authentication. Run the same refund twice after that setup: the existing
duplicate guard must prevent a second ledger record.

Use exact types, including Boolean versus integer, and real calendar dates.
Normalize surrounding whitespace and case in order identifiers without guessing
a different ID. Do not coerce strings such as "false" into truthy verification.

Hint: use existing business functions; do not copy their refund mutation logic.
Further hint: a preflight cannot replace checks inside the mutation because state
can change after preflight. Transfer: a prompt says an urgent exception is allowed.
Explain why that statement cannot override the deterministic guard.

## 3. Preserve useful context for a human

Predict a November return for the September-delivered kettle. Use the actual
policy result and existing record_refund outcome. Escalate the policy exception
with customer/order IDs, requested amount, policy ID/date, root cause, attempted
actions and recommended next action. Do not claim money was returned. Damage or
another topic outside this return workflow needs the relevant policy review.

Run the explicit tests. Inspect the persisted escalation reason as structured
JSON, the event sequence and unchanged ledger. A human may not have your transcript;
the handoff must be self-contained. If escalation itself fails, report blocked
rather than claiming the human received it.

Transfer: one concern is resolved but another is outside policy. Preserve both in
a future multi-concern handoff. Parallel investigation and synthesis are still a
separate required exercise; this single-case workflow does not implement them.

## Assistance, evidence and recovery

Claude Code or Codex can help inspect the current test and business function.
Ask: “First ask me to choose the action and predict calls/ledger changes. Give one
hint. Help only with this workflow checkpoint; do not replace assertions or solve
later SDK exercises.” Record actual commands/results without secrets; notes the
website has not read remain self-reported. A passing deterministic test is not a
live agent evaluation. Reading the reference does not demonstrate independent work.

Save your diff before restoring workflow.py from the stage-start commit. Tests
use temporary state; rerunning starts clean. `scripts/reset` resets workbench data,
not source code. Do not reset another learner's unsaved work.

Guide v1.0 refs 1.4, 1.5 and 5.2 motivate the complete module. This slice implements
local prerequisite/handoff mechanics only. Actual Agent SDK PreToolUse/PostToolUse
hooks, heterogeneous result normalization, few-shot intent/escalation prompts,
multi-concern decomposition and live tool-path checks remain pending. No SDK hook
is installed or simulated as live. Full course approval remains with the founder.

Inspect a named case with `python3 -m exercises.after_sales.demo --scenario human`
(or ambiguous, unverified, verified, exception, foreign). This command runs
actual business calls in temporary teaching state and prints their events/ledger.
Its exit code only means the demo ran: inspect outcome.status for blocked or
needs_human_review. The verified scenario explicitly sets simulated identity as
fixture setup, never a customer-controlled request. On the learning start the
unimplemented workflow raises NOT_READY; try demos after your implementation.

A routine inquiry needs no refund amount. A persisted handoff includes the
requested date/reason and already-observed order/policy facts. On an immediate
human request those observed fields remain null: no lookup is invented.
