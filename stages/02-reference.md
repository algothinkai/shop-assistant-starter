# Stage 2 reference — compare after predicting

Start: f957cb7109ede5e940160062034c87fce4e9ad64.
Only loop.py completes the exercise. Preserve assistant blocks, dispatch every
allowlisted request, append all matching results as the next user message, then
ask the model again. Reject malformed or reused IDs before any dispatch in that
response. Normal end_turn ends generation; it does not certify business resolution.
Abnormal stops, transport failures and the safety bound remain interrupted.

Run scripts/verify-stage 2 (14 offline checks), scripts/test and Stage 0/1. Also
inspect happy/multiple/missing/truncated demo transcripts. The last exits 1 on
purpose. No real model was contacted. Current API docs, fixed endpoint/version,
local environment requirements and live recovery are in 02-tool-loop.md.

Compare your prediction with history and local_tool_events, not merely the final
sentence. Explain why tool errors survive a later end_turn and why no tool runs
from a truncated response. Reading this solution is assisted, not mastery.
