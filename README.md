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
  This branch adds the separate Stage 1 exercise. Stages 3–10 say NOT_READY;
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
