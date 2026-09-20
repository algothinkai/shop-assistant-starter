# Stage 10 — combined faults and transfer

Draft learning start: `codex/stage-10-capstone-start`. The separate reference is
`codex/stage-10-capstone-reference`; exact commits are bound in algothink. Work in
your own copy. Python3.12+ standard library; `scripts/test` is the runnable
foundation. No provider key or live model is needed for the local challenge.

This is a **fictional authored casebook**, not a transcript from a model or shop.
Six changed situations reuse the earlier business/tool/receipt/research/review
skills. C1–C5 together mention every one of Guidev1.0's 30 task statements; C6
asks for another developer-setting transfer. This mapping is a design checklist,
not proof that all 30 skills have been demonstrated. No online judge, payment or
real customer record is used.

## Independent challenge

Read `exercises/capstone/cases.json` one case at a time. Before viewing hints or a
reference, write in `response.json`:

1. Your choice among that case's options and **why** it fits the facts. Explain at
   least one tempting alternative you rejected.
2. Predict the observable result of your action, including what remains unknown.
3. List the case's evidence keys you actually inspected. Copying keys is not proof
   you ran an earlier exercise; the learning site will mark unread local work as
   self-reported.
4. Reconsider the changed transfer situation; choose and explain again.

Start with C1's customer request and missing tool_result. A safe plan must not
execute a refund on ambiguous order/identity/policy inputs, even if the customer
wants urgency. C2 asks whether schema-valid extraction can still contradict text.
C3 asks how to present policy conflict and a failed delegate. C4 asks whether
an old scratchpad can authorize a current edit. C5 combines valid-looking JSON
with failed terminal review and a prior issue. C6 moves to another code path with
scoped instructions and a weak zero-only test. Each case has multiple simultaneous
constraints; solve them together rather than matching one feature name.

Run relevant earlier demonstrations when you need local evidence, for example:

```sh
scripts/test
scripts/verify-code-review
scripts/verify-review-host
scripts/verify-review-quality
scripts/verify-review-ci
scripts/verify-capstone
python3 -m exercises.capstone.workflow exercises/capstone/response.json
```

Earlier stage checks verify their own authored contracts. Some tool stages need
their pinned optional environment; if unavailable, record exactly which check was
not run. Do not cite a fixture as live Claude/Codex proof. The capstone CLI checks
six response shapes and case evidence keys; `STRUCTURE_ONLY` and `UNVERIFIED`
mean a human/course review must still judge reasoning and actual practice. A
perfect structural report does not mean mastery or certification readiness.

Checkpoint prompts for Claude Code and Codex are the same: "Ask me to choose and
predict for **this case only**, then ask for my reason. Review my cited evidence
against its source and give one hint. Do not supply the other cases or a complete
response file." Tool-specific live behavior must be checked separately. Manual
work follows the same acceptance.

## Inspect and recover

Compare your prediction with the source record and stage output. For each case,
record the exact command/commit, what the output actually said and one remaining
uncertainty. Do not alter earlier stage implementations to make a response appear
correct. A local file the learning site did not read remains self-reported.

If you make a mistake, save your reasoning, reset only `response.json` to the
starter template in a new checkout, then retry the specific case. Do not reset
shop ledger or other stage work merely to erase an incorrect choice. The reference
holds one author-draft answer set; it is separate so the learning start does not
reveal all decisions. Founder approval of course/rubric is still required.

Source: founder-supplied Exam Guidev1.0 and original fictional Shop Assistant
situations. The 30 refs are exact guide identifiers; local cases do not claim
live Claude, MCP, SDK, CI model or batch provider integration.
