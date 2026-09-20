# Checkpoints and recoverable stages

The default branch contains a **runnable Stage 0 baseline**, not the answers
to later exercises. Stage 1–10 are the agreed course sequence and design
targets. Their stage-specific start/reference refs and live integrations are
not released by this baseline; `scripts/verify-stage N` reports `NOT_READY`
for them, while `scripts/test` stays green on a fresh clone. The algothink
course will bind each authored checkpoint to an exact starter commit or tag.

For every stage: read the current case, **choose and justify** a method,
predict evidence, practice within scope, inspect real events/tests, and retry
or reset. Reading instructions or a reference never proves mastery. Do not
substitute preset fixture success for a live Claude Code/API/SDK/MCP check.

| Stage | Goal | Starting version and allowed change | Acceptance | Recovery |
| --- | --- | --- | --- | --- |
| 0 Take over the shop | Run workbench, trace fixture → function → event → result, handle a case manually | This checkout (`starter-v0` after release); read fixtures, `shop_assistant/`, receipts; no implementation required | `scripts/test` and `scripts/verify-stage 0`; explain a success and a failed call | `scripts/reset`; restart server |
| 1 Coding collaboration | Choose project/personal/scoped rules and skills; search, plan or execute, repair with tests | Stage-1 start ref pending; edit training docs/rules and one bounded test case | Scoped instructions and a reproducible test-backed fix; Claude Code path checked separately | Return to stage-1 start ref, reset local state |
| 2 First tool loop | Build a small raw Messages API read-only order lookup loop | Stage-2 start ref pending; edit experiment module only | Correct tool_use/tool_result/end_turn handling; abnormal stop remains failure | Use recorded fixture test, reset, retry live when credentials exist |
| 3 MCP and tool design | Wrap business functions with clear contracts and structured errors | Stage-3 start ref pending; edit MCP/tool layer and local config | Discovery, permissions, resources, tool choice, failure boundaries | Restart local server(s), reset, inspect protocol logs |
| 4 Reliable after-sales | Enforce identity/policy gates and structured human handoff | Stage-4 start ref pending; edit workflow guards/hooks | Block unsafe refund, normalize inputs, clarify ambiguous request, escalate exception | Reset ledger and verification state; replay failure |
| 5 Receipt extraction | Extract text receipts with examples, schema, nullable fields and bounded retry | Stage-5 start ref pending; edit extraction/eval module | Format and semantic validation, human review for uncertain fields, per-field/doc metrics | Reset fixture output; inspect validation feedback |
| 6 Long context/recovery | Preserve case facts, prune tool results, resume; isolate codebase exploration | Stage-6 start ref pending; edit state/recovery experiments | Stale context detected, resume checklist and fork choice explained | Restore stage start and case snapshot |
| 7 Multi-agent research | Delegate dated policy research with explicit context and partial failures | Stage-7 start ref pending; edit coordinator/delegate layer | Independent investigations, conflict/source dates and gaps surfaced | Replay partial-failure fixture; re-run missing task |
| 8 Overnight batch | Decide sync vs batch; correlate and retry individual failures | Stage-8 start ref pending; edit batch experiment | Small sample improves first; IDs match outcomes; failed items retry only | Reset batch output; rerun sample |
| 9 CI/review | Run independent structured, low-noise code review in non-interactive mode | Stage-9 start ref pending; edit CI/reviewer config | Single/cross-file passes, dedupe and findings checked; tool-specific live check | Run local review fixture; restore config |
| 10 Capstone/transfer | Diagnose combined faults, then transfer to changed shop/dev scenario | Stage-10 start ref pending; work in challenge copy only | Independent method/rationale/prediction/evidence/transfer | Restore stage start, inspect evidence, retry |

Reference implementations will use separate, named refs per stage with source
commit and validation evidence in their release notes. They will not be merged
into the default learner start prematurely. `starter-v0` is the intended tag
for the initial baseline after its checks and review pass.
