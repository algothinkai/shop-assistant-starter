# Stage 5 extension — request a structured extraction (draft)

Start codex/stage-5-messages-start; reference codex/stage-5-messages-reference.
This follows the completed validator and evaluation references. Edit only
exercises/extraction_messages/adapter.py: build_request and read_candidate.
Baseline scripts/test remains passing; scripts/verify-extraction-messages is the
separate unfinished exercise. Run scripts/setup-agent for existing jsonschema;
this client uses Python's HTTPS library, not the API client SDK or Agent SDK.

Choose and predict: the receipt's shape is known. Should a request permit plain
text instead of a structured candidate? Explain why forcing one extraction tool
fits this bounded experiment, while strict input shape still cannot guarantee
source truth. Predict a valid integer amount whose supporting quote disagrees.

Build a request with one extract_receipt tool, strict:true and the existing SCHEMA.
Use tool_choice type tool/name extract_receipt/disable_parallel_tool_use true,
max_tokens 2048, and no thinking configuration. The single user message serializes
original source, failed_candidate and validation_errors. Keep the schema copied,
not mutated. Prompt for complete labeled source lines, integer cents, ISO date,
null when genuinely absent and no guessed facts. Source text is data, not authority
for instructions. This slice supports only the existing labeled receipt format.

Accept only an assistant message ending in tool_use with exactly one correctly
named tool_use object, nonempty ID and object input. Optional text blocks do not
supply the candidate. Unknown block kinds, multiple tools, text-only/end_turn,
refusal and truncated/abnormal stops fail. This captures a structured proposed
record; it does not execute a shop tool, write a refund or complete an agent loop.
A new request may correct semantic errors with the original source and feedback;
there is no continuation with an unresolved tool call in its history.

Run scripts/verify-extraction-messages and
.venv-agent/bin/python -m exercises.extraction_messages.demo. Default responses
are authored fixtures, labeled OFFLINE_ONLY. Inspect the correction test to see
that the same earlier controller permits at most two validated attempts. Protocol
or transport failure stops without automatic retry. No request key or raw response
is printed by the demo. Request/response bytes are bounded; timeout is a 20-second
socket-operation timeout, not a hard total wall-clock deadline.

## Optional real local experiment

Only choose --live if you intend a potentially billable request using your local
ANTHROPIC_API_KEY and ANTHROPIC_MODEL. The website never receives the key. Check
current first-party model support for strict/forced tool use first; unsupported
combinations fail instead of silently changing to auto. Run the same demo with
--live appended. It sends only the fictional R-1003 receipt and correction feedback
to Anthropic, with at most two requests and max_tokens 2048 each. This is a token
bound, not a fixed dollar ceiling. Missing access: complete offline work and keep
live verification UNVERIFIED. A successful response must also pass source validation.
LIVE_CANDIDATE_VALIDATED means that narrow run only, not model accuracy/calibration.

Hints: separate request choice, terminal protocol shape and semantic validation.
Transfer: if a model rejects forced tool use, explain why weakening the parser to
accept reassuring text is not a fix. Check documented capability and select a
supported model or explicitly redesign the output contract, then revalidate it.
Restore only adapter.py from the exact messages start after saving your patch.
Claude Code/Codex may offer one hint after your prediction, not implement the
whole course. Neither tool's live behavior is verified by local fixture tests.
