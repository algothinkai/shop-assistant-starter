# Checkpoints and recoverable stages

The Stage 0 baseline stays on its own branch. This branch adds the Stage 1 draft
exercise; its explicit checks intentionally fail before repair. Stages 6–10 remain
NOT_READY. The course binds stage starts and references to exact commits.

For every stage: read the current case, **choose and justify** a method,
predict evidence, practice within scope, inspect real events/tests, and retry
or reset. Reading instructions or a reference never proves mastery. Do not
substitute preset fixture success for a live Claude Code/API/SDK/MCP check.

| Stage | Goal | Starting version and allowed change | Acceptance | Recovery |
| --- | --- | --- | --- | --- |
| 0 Take over the shop | Run workbench, trace fixture → function → event → result, handle a case manually | This checkout (`starter-v0` after release); read fixtures, `shop_assistant/`, receipts; no implementation required | `scripts/test` and `scripts/verify-stage 0`; explain a success and a failed call | `scripts/reset`; restart server |
| 1 Coding collaboration | Choose project/personal/scoped rules and skills; search, plan or execute, repair with tests | codex/stage-1-start; report.py plus additive checks and scoped training instructions | Scoped instructions and a reproducible test-backed fix; Claude Code path checked separately | Return to stage-1 start ref, reset local state |
| 2 First tool loop | Build a small raw Messages API read-only order lookup loop | codex/stage-2-start; edit exercises/tool_loop/loop.py only | Correct tool_use/tool_result/end_turn handling; abnormal stop remains failure | Use recorded fixture test, reset, retry live when credentials exist |
| 3 MCP and tool design | Wrap business functions with clear contracts and structured errors | codex/stage-3-start; edit exercises/mcp_shop/actions.py | Discovery, permissions, resources, tool choice, failure boundaries | Restart local server(s), reset, inspect protocol logs |
| 4 Reliable after-sales | Enforce identity/policy gates and structured human handoff | codex/stage-4-start; edit exercises/after_sales/workflow.py | Block unsafe refund, normalize inputs, clarify ambiguous request, escalate exception | Reset ledger and verification state; replay failure |
| 5 Receipt extraction | Extract text receipts with examples, schema, nullable fields and bounded retry | codex/stage-5-start; edit exercises/extraction/validation.py | Format and semantic validation, human review for uncertain fields, per-field/doc metrics | Reset fixture output; inspect validation feedback |
| 6 Long context/recovery | Preserve case facts, prune tool results, resume; isolate codebase exploration | Stage-6 start ref pending; edit state/recovery experiments | Stale context detected, resume checklist and fork choice explained | Restore stage start and case snapshot |
| 7 Multi-agent research | Delegate dated policy research with explicit context and partial failures | Stage-7 start ref pending; edit coordinator/delegate layer | Independent investigations, conflict/source dates and gaps surfaced | Replay partial-failure fixture; re-run missing task |
| 8 Overnight batch | Decide sync vs batch; correlate and retry individual failures | Stage-8 start ref pending; edit batch experiment | Small sample improves first; IDs match outcomes; failed items retry only | Reset batch output; rerun sample |
| 9 CI/review | Run independent structured, low-noise code review in non-interactive mode | Stage-9 start ref pending; edit CI/reviewer config | Single/cross-file passes, dedupe and findings checked; tool-specific live check | Run local review fixture; restore config |
| 10 Capstone/transfer | Diagnose combined faults, then transfer to changed shop/dev scenario | Stage-10 start ref pending; work in challenge copy only | Independent method/rationale/prediction/evidence/transfer | Restore stage start, inspect evidence, retry |

Reference implementations will use separate, named refs per stage with source
commit and validation evidence in their release notes. They will not be merged
into the default learner start prematurely. `starter-v0` is the intended tag
for the initial baseline after its checks and review pass.

Stage 1 draft now has separate `codex/stage-1-start` and
`codex/stage-1-reference` refs. Read [its checkpoints](01-collaboration.md).
On these branches, verify-stage 1 runs explicit exercise checks (expected failure
before repair); stages 6–10 remain NOT_READY. Baseline tests stay green.

Stage 2 draft has separate codex/stage-2-start and codex/stage-2-reference refs.
Read [the tool-loop checkpoint](02-tool-loop.md). On these refs verify-stage 2
runs offline protocol checks; live API use is separately opt-in and unverified.

Stage 3 adds an optional pinned MCP environment and two real local stdio servers.
Read [the MCP checkpoints](03-mcp.md) before running `scripts/setup-mcp` and
`scripts/verify-stage 3`. The start dispatcher intentionally returns NOT_READY;
the baseline remains green. Live Claude Code/model behavior is separately unverified.

Stage 4 learning start builds on the completed Stage 3 reference. Read [Stage 4](04-after-sales.md) for the deterministic workflow exercise.
Only `scripts/verify-stage 4` intentionally fails before implementation; foundation
checks stay passing. Agent SDK hooks are not yet implemented or verified.

Stage 5 now has separate start/reference validator branches. Read
[the receipt exercise](05-extraction.md). scripts/verify-stage 5 and
scripts/verify-extraction run the same explicit checks; start failures are
intentional. Full model extraction/evaluation coverage remains pending.
