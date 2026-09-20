# Stage 3 — Make tool boundaries observable

Draft learning start: `codex/stage-3-start`, based on Stage 2's reference.
The separate `codex/stage-3-reference` contains the completed dispatcher.
Only edit `exercises/mcp_shop/actions.py` during this exercise. Keep the supplied
checks unchanged; add your own checks when a prediction needs evidence.

MCP is a protocol through which a client discovers and calls tools or reads
resources from a server. This lab runs two real local stdio server processes;
stdio carries protocol messages, not a model response. No API key is needed.

## Prepare and predict

```sh
scripts/test
scripts/setup-mcp
scripts/verify-stage 3
```

The foundation tests pass. Stage 3 explicitly fails until you implement its
NOT_READY dispatcher. The optional `.venv` pins MCP Python SDK 2.2.0 and its
transitive dependencies; Stage 0 still uses only the standard library.
If installation is unavailable, inspect contracts and write predictions, label
runtime evidence unverified, then resume setup when dependencies are available.

## Checkpoint 1 — Choose a tool from its contract

A customer provides order O-1001. Another only provides customer C-9999. Choose
between `get_order` and `find_orders`, explain why, and predict the different
result shapes. Read `contracts.py`: purpose, required arguments and exclusions
belong in the tool description/schema, rather than a growing keyword-routing
prompt. A single vague `shop_action` would hide those distinctions.

Implement scoped dispatch using the existing shop functions/catalog. Validate
arguments before dispatch: reject extra properties and wrong types; validate
calendar dates as well as their string shape. Never add refunds to these profiles.
Run the explicit checks and inspect each failure before changing another branch.

Hints, in order: inspect `PROFILES`; inspect each `input_schema`; then inspect
`ShopError` in the business layer. Use the supplied `result`/`failure` helpers.
Recovery: save your diff, restore only `actions.py` from the start ref, and retry.

Transfer: a customer can have several orders. Explain why a successful empty
search is different from a failed exact lookup, and what question you would ask
before choosing an order. Do not silently select the first returned order.

## Checkpoint 2 — Recover only when the error permits it

Predict outcomes for a malformed ID, missing order, denied tool and one temporary
outage. Use structured `isError` plus `errorCategory`, `code`, `isRetryable` and
`message`; do not return a success-shaped apology. Categories are validation,
business, permission and transient. Missing order is business/non-retryable;
malformed input is validation/non-retryable; denied access is permission.

```sh
.venv/bin/python -m exercises.mcp_shop.smoke
scripts/verify-stage 3
```

The smoke command prints observations, including failures: exit zero alone is
not acceptance. Inspect structured results and the attempt list. The fixed
`--transient-once` server flag injects one error; the client allows at most two
attempts. `--deny` simulates local tool permission denial, not authentication.
Do not retry validation, permission or missing-order errors unchanged. The local
profile enforces tool scope; `readOnlyHint` is advisory and grants no permission.
Each process uses temporary teaching state; no real money or external store exists.

Transfer: retries still fail. Preserve the failure for the caller instead of
returning an empty successful result. Module 7 will apply this rule across agents;
this local exercise alone does not verify coordinator failure propagation.

## Checkpoint 3 — Discover two servers and choose context deliberately

Predict which tools and resources each profile advertises. Inspect smoke output:
orders exposes `get_order`/`find_orders`; policies exposes `get_policy` and the
`shop://policies/catalog` resource. Read the catalog's version dates, then query
the applicable policy date. A resource provides application-selected context;
a tool performs a model-selected action. Neither category guarantees trust.

Inspect `.mcp.example.json`. It is a template, not installed configuration. To
try Claude Code deliberately, set `SHOP_ROOT` to this absolute checkout and
`SHOP_PYTHON` to its `.venv/bin/python`, then use the template as project
`.mcp.json`. Keep personal paths/credentials out of shared commits. Current
Claude Code distinguishes project `.mcp.json` from private local/user entries
in `~/.claude.json`; local is project-specific, user is cross-project. Do not
rewrite existing personal configuration. Check missing variables before launch.
Use `/mcp` to inspect actual connection status and discovered tools. Record that
separately from Python client results; unavailable Claude Code means unverified.
Evaluate existing trusted community servers for standard integrations before
building another server; these custom tools exist for the fictional shop contract.

Inspect `model_settings.py`: `auto` permits model choice, `any` requires a provided
tool, and `tool` names a specific scoped tool. Force an initial order lookup only
when the workflow requires it, then restore appropriate follow-up choice so the
model can finish. These are API request-shape checks, not a live model test.
Support depends on the chosen model/thinking settings; verify current docs before
using forced choice. MCP discovery itself does not set Anthropic `tool_choice`.

Transfer: the policy role needs no order access. Limit its provided tools and
server dispatch scope; a prompt asking it to avoid orders is insufficient.
Explain when resource context saves exploratory calls and when dated lookup is
still required. Merely discovering both servers does not grant every role both.

## Bounded assistance and recovery

For Claude Code or Codex: “Ask me to choose the current checkpoint's method and
predict evidence first. Inspect only its contracts, business function and failing
check. Give one hint before proposing an edit to actions.py. Do not solve later
checkpoints or replace tests. Tell me what the observed run proves.”

Codex can perform the same file/terminal exercise. Its success does not verify
Claude Code's configuration scopes or `/mcp`. The Python client is the recovery
path for either missing host tool. No host-specific configuration is automatically
installed. Reading the reference or reporting a run is not independent mastery;
the algothink site labels evidence it has not read as self-reported.

Save your patch before restoring code. `scripts/reset` resets workbench state,
not source files; restart the MCP command to reset its temporary state/fault.
After your attempt, compare the separate reference branch and rerun the same
checks. The default workbench remains the preset demonstration.

## Version and verification sources

Guide coverage source: Claude Certified Architect – Foundations Exam Guide v1.0,
objectives 2.1–2.4. Current implementation uses MCP Python SDK 2.2.0 (v2 callback
API, not v1 decorators); local protocol checks target 2026-07-28. SDK attributes
use snake_case while wire results use aliases such as `isError`/`structuredContent`.
First-party sources checked 2026-09-20:

- https://github.com/modelcontextprotocol/python-sdk
- https://py.sdk.modelcontextprotocol.io/client/
- https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- https://modelcontextprotocol.io/specification/2026-07-28/server/resources
- https://code.claude.com/docs/en/mcp
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools

Local protocol tests, API request-shape tests and live Claude host/model behavior
are separate evidence categories. This stage does not claim Agent SDK execution.
