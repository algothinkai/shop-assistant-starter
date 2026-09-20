# Stage 2 — First client-tool loop

Draft, Exam Guide v1.0 task 1.1. This stage starts after Stage 1 and reuses the
same fictional shop and get_order function. No MCP or Agent SDK yet. A client
SDK is a library for calling an API; Agent SDK manages a broader agent runtime;
Claude Code is a coding tool. This small experiment sends Messages API requests
directly with Python standard-library HTTPS so you can see the loop. Client SDK
Tool Runner helpers also exist; hand-writing every production loop is not required.

Start: codex/stage-2-start. Reference: codex/stage-2-reference (separate answer ref).
Only exercises/tool_loop/loop.py is the learner implementation. Checks, fixtures,
read-only dispatcher and HTTPS transport are provided. Baseline scripts/test and
verify-stage 0/1 remain green. scripts/verify-stage 2 initially has expected
NotImplemented errors for loop cases; the transport checks can already pass.

## A. Predict a request/result pair

A response has text plus a tool_use block. Before coding, identify the execution
ID, tool name and arguments. Does the text mean the workflow ended? Predict the
next history messages. Read fixtures.py, tools.py and the real get_order method.
A tool_result must refer to the exact tool_use ID, not its tool name or order ID.
Keep the assistant content, then append a user message containing all results
immediately after it. Inspect multiple calls in one turn and another later turn.

Implement the loop in small steps and run scripts/verify-stage 2. Execute
`python3 -m exercises.tool_loop.demo --scenario happy` after a passing repair.
The output labels authored_fixture_no_model and includes actual local function
call/result events. Predict those events before running. No fictional response
in fixtures.py is represented as captured Claude behavior.

## B. Distinguish ended, interrupted and resolved

Run scenarios missing, multiple and truncated using the same --scenario command.
Predict: missing order returns is_error with ORDER_NOT_FOUND; multiple pairs every
ID and continues; truncated never executes its partial tool request. end_turn
means the model turn ended, not that the support case was resolved. Text such as
“All done” is not a stop protocol. No text at end_turn still ends the turn.

Handle unknown/malformed blocks or duplicate IDs explicitly; dispatch only
get_order. Return structured invalid-name/argument errors as tool results. Never
infer a refund, use an arbitrary function name as code, or hide a tool failure.
max_tokens, refusal and other abnormal stops interrupt this small experiment.
pause_turn is associated with server tools; these are outside Stage 2. Stop and
inspect it rather than implement a pretend server continuation. A six-turn safety
bound prevents runaway cost; reaching it is interruption, never successful normal
completion. The primary normal stopping rule remains end_turn. Save the transcript
and explain how a different stop reason changes the next action.

## C. Optional real request, distinct evidence

The default is offline. Real mode is explicit:
`python3 -m exercises.tool_loop.demo --live`.
Set ANTHROPIC_API_KEY and an available ANTHROPIC_MODEL in your local shell first;
the blank .env.example is documentation, not an auto-loaded key file. Never paste
keys into algothink. Real API requests may incur cost: up to six requests with a
512 output-token cap each, plus input charges. No model is silently selected.
Record the exact model, API version, request result and matching local events;
confirm your current account/model supports the tool before running.

The adapter uses fixed HTTPS /v1/messages, API version 2023-06-01, 20-second socket
timeout, bounded payloads and no redirects or automatic retries. A transport failure
is an explicit interruption. Diagnose credentials/model/limits locally; do not
switch silently to fixtures and call it live success. If no credential is available,
keep live UNVERIFIED and finish the offline checkpoint; return later to this lab.
The transcript text is model output, not a guarantee of correct support reasoning.

Both Claude Code and Codex may help implement this same Python exercise. Use the
current checkpoint prompt: “Ask for my predicted stop reason, message roles and
IDs first. Wait. Help change only loop.py, using the failing assertion. Do not
open the reference or solve the transfer before I try.” Neither coding tool's
operation certifies the other, and neither is the Messages API agent runtime.

## Acceptance and recovery

Run scripts/verify-stage 2, scripts/test and verify-stage 0/1. All offline cases
must pass on the reference. Inspect same-ID result pairing, real local calls,
explicit interruption and unchanged teaching ledger. Logs supplied to the site
are self-reported until it actually reads an artifact. Hint/reference use is assisted.

Save your diff before resetting. Restore only loop.py from codex/stage-2-start to
restart; scripts/reset clears shop state, not code. Each demo uses disposable state.
Compare the reference in a separate worktree only after your attempt. Transfer:
a response has reassuring text, two tool requests and max_tokens; decide whether
any tool should run, what evidence is missing and why increasing a limit would
require another deliberate attempt rather than declaring success.

Current first-party sources checked 2026-09-20:
[handling client tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls),
[stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons),
[Messages request](https://platform.claude.com/docs/en/api/messages/create).
Guide v1.0 supplies the objective, not a frozen list of every current stop reason.
Unknown reasons fail explicitly here. Streaming, server tools, extended thinking,
SDK-managed loops and resuming paused server turns are outside this first lab.
No live request was run by the author for this draft.
