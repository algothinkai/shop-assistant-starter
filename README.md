# Shop Assistant starter

A small **fictional** coffee-equipment support workbench for algothink's
Claude Certified Architect – Foundations course. Stage 0 is runnable today.
The workbench lets you choose a ticket, inspect local facts, run a **fixed
preset demo**, and see the actual local business-function call and error events.
The preset does **not** call Claude, Claude Code, Codex or another model.

Use Python **3.12+ on macOS or Linux**. The baseline has no third-party
dependencies or install step. From the repository root:

```sh
python3 -m shop_assistant serve
```

Open <http://127.0.0.1:8765>. The server binds loopback only. Select a ticket,
predict what the preset will do, then press **Run preset demo**. Inspect the
run ID, function calls, results, errors and local ledger. A refund demo never
charges or returns real money; it only writes `.local/state.json` if its local
teaching guards pass. From reset state, the blocked-refund ticket leaves the
ledger unchanged; if you later set its simulated identity to verified, that
same local call may succeed. Check the event log and ledger each time.

Other commands:

```sh
scripts/test             # Foundation unit tests; expected to pass on a fresh clone
scripts/verify-stage 0   # Stage 0 observable baseline check
scripts/verify-stage 1   # Stage 1 exercise: intentional failures until repaired
scripts/reset            # Restore empty local teaching state and event history
python3 -m shop_assistant demo T-1001  # Run a preset from the terminal
```

The same commands have `python3 -m shop_assistant test`, `verify-stage N`, and
`reset` forms. If port 8765 is in use, run
`python3 -m shop_assistant serve --port 8766`. Stop with Ctrl-C. Reset while
the server is stopped to avoid concurrent local changes. `.local/` and `.env`
are ignored by Git. If `.local/state.json` is corrupted, stop the server and
run `scripts/reset` to replace it. `.env.example` contains only an empty
placeholder; Stage 0
does not read a key. Future API credentials belong only in your local `.env` or
shell, never on the algothink website or in screenshots.

## What you are seeing

- `shop_assistant/fixtures/`: invented products, customers, orders, tickets and
  dated policy versions. Text receipts are in `receipts/`.
- `shop_assistant/business.py`: directly callable shop functions that later
  stages can wrap as model tools or MCP tools. They return local data or raise a
  structured `ShopError`.
- `ShopService.run_preset` in `shop_assistant/business.py`: fixed preset flow
  using those real functions. It records actual call/result/error events; its
  text is labelled preset output.
- `shop_assistant/web.py`: local HTML workbench. It is a viewer and demo trigger,
  not a hosted agent or commerce backend.
- `stages/README.md`: stage goals, allowed edits, acceptance and recovery.
  This branch adds the separate Stage 1 exercise. Stages 5–10 say NOT_READY;
  the fresh-install baseline test suite remains green.

Identity verification is a **simulated Boolean in local teaching state**, never
a claim of real customer authentication. `record_refund` checks that state and
the dated return policy, then appends to a teaching ledger. No payment API is
configured. The workbench uses made-up names and amounts and sends no data to
algothink or other servers. If a preset fails, its error event and overall
result say so; a fixture passing does not prove any live Claude integration.

The main learning route is stage-by-stage. [Reference versions](stages/README.md)
are tracked separately as later stages are authored, so opening this default
checkout does not reveal every future answer. The complete course, rubrics and
mock exams live in the separate algothink repository and require founder
approval before public use.

This is a **Stage 1 draft branch**. The Stage 0 description above remains the
foundation; see [Stage 1](stages/01-collaboration.md) for its separate start and
reference, intentional exercise failures, scope and recovery.

This Stage 2 branch builds on the completed Stage 1 reference. See
[Stage 2](stages/02-tool-loop.md) for explicit offline/live commands and recovery.
The default workbench remains a fixed preset, not the Messages API experiment.

Stage 3 adds an optional pinned MCP environment and two real local stdio servers.
Read [the MCP checkpoints](stages/03-mcp.md) before running `scripts/setup-mcp` and
`scripts/verify-stage 3`. The start dispatcher intentionally returns NOT_READY;
the baseline remains green. Live Claude Code/model behavior is separately unverified.

This is the **Stage 3 reference branch**. Attempt `codex/stage-3-start` first.
The scoped dispatcher is implemented here; `scripts/verify-stage 3` uses the same
checks as the start. Local protocol success does not validate a Claude model or
host connection, and does not approve the draft curriculum for publication.

Stage 4 learning start builds on the completed Stage 3 reference. Read [Stage 4](stages/04-after-sales.md) for the deterministic workflow exercise.
Only `scripts/verify-stage 4` intentionally fails before implementation; foundation
checks stay passing. Agent SDK hooks are not yet implemented or verified.

This is the **Stage 4 reference branch**. The deterministic workflow is complete
for the documented local slice and passes the start's same checks. Attempt the
separate codex/stage-4-start before comparing this reference. SDK hooks, live
intent interpretation and the complete Module 4 course remain pending.

The Stage 4 hooks extension has separate start/reference branches and an optional
Agent SDK environment. See [the hook checkpoints](stages/04-agent-hooks.md).
`scripts/verify-hooks` is separate from the passing baseline/workflow checks.
No SDK/model call occurs unless the learner deliberately selects `--live`.

This is the **Stage 4 hooks reference branch**. The two callbacks are implemented;
`scripts/verify-hooks` passes the same checks provided on its separate start.
All recorded runs are offline. An actual model-driven hook round trip remains
UNVERIFIED until the explicit local live experiment observes both callbacks and a
successful terminal result.

Stage 5 adds a separate receipt-validator learning start/reference. See
[the extraction checkpoint](stages/05-extraction.md). Run scripts/verify-extraction
in the optional pinned environment. Authored candidates are fixtures, not model
output; no live extraction quality or calibrated confidence is claimed.

This is the **Stage 5 reference branch**. The narrow receipt validator is
implemented and passes the same checks as the learning start. Complete source
lines, unresolved source values and bounded correction are checked; this is not
model extraction, arithmetic reconciliation or calibrated automation.

Stage 5 evaluation has a separate [start/reference exercise](stages/05-evaluation.md).
Run scripts/verify-extraction-eval only when attempting that checkpoint. Its authored
predictions teach metrics/calibration mechanics; they do not measure a live model.

This is the **Stage 5 evaluation reference**. Its dedicated evaluation checks pass;
attempt codex/stage-5-evaluation-start before comparing the implementation. Calibration
and held-out data remain tiny authored examples, not evidence for deployment.

Stage 5 Messages extraction has separate [start/reference instructions](stages/05-messages.md).
The default demo uses an authored response. Only explicit --live sends a potentially
billable request using learner-local credentials; compatibility is not yet live-verified.

This is the **Stage 5 Messages reference**. Request construction and terminal
candidate parsing pass the same offline checks as the learning start. Actual API
compatibility and live receipt extraction remain UNVERIFIED; the default demo
never calls a model. Attempt the separate messages start before reading this answer.
