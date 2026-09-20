# Stage 6 extension — Agent SDK resume and fork (draft)

Start codex/stage-6-sessions-start; reference codex/stage-6-sessions-reference.
Run scripts/setup-agent for the existing pinned Python Agent SDK0.2.157.
Foundation scripts/test still passes; scripts/verify-sessions is the dedicated
unfinished exercise. Edit only choose_action, build_options and consume in
exercises/sessions/adapter.py. Do not change the supplied probe or test answers.

## Choose, explain, predict

Continue picks the most recent session; resume selects a recorded ID. With multiple
cases, choose explicit resume to avoid the wrong conversation. Fork starts another
conversation from that history so you can explore an alternative. Predict which
IDs should match across fresh → resume → fork → resume-original.
Conversation branches share the filesystem: a fork is not an isolated checkout or
file rewind. This experiment disables tools and never edits a business record.

choose_action validates the requested fresh/resume/fork mode. For resume/fork,
require a valid prior session ID and compare complete tracked source-version maps.
Changed/added/removed sources return fresh, not a silent reuse of stale tool results.
Fresh means start with a newly checked summary and explicit remaining unknowns,
not reuse an old summary as current truth. The caller must reread changed sources;
this planning helper cannot verify untracked data or regenerate a summary.

build_options sets resume=None/fork_session=False for fresh; uses the recorded ID
for resume; adds fork_session=True for fork. Never continue_conversation implicitly.
Use the supplied existing directory and explicit model, tools=[], mcp_servers={},
strict_mcp_config=True, setting_sources=[], two turns and max_budget_usd0.10 per call.
Discard CLI stderr; do not print model/auth errors. No bypass-permissions setting.
SDK options construction is not proof that a CLI session ran.

consume reads the whole asynchronous message stream and requires exactly one
successful ResultMessage with valid session_id. is_error or abnormal stop/terminal
reason remains failed. Capture a valid ID even on failure, without exposing result
text or errors; an ID alone is not success. Missing/duplicate results, exceptions
(including after a result), or invalid IDs fail. Do not swallow cancellation.
Success returns status=success, session_id and text; failure returns status=failed,
session_id orNone and text=None. SDK IDs are validated as UUIDs in this lab.

## Practice and evidence

Run scripts/verify-sessions then
.venv-agent/bin/python -m exercises.sessions.demo. The default is OFFLINE_ONLY:
authored SDK objects test option wiring and terminal checks, not memory or real
transcripts. Predict each ID relationship and explain why the last prompt omits
the amount: it tests the original conversation after the alternative branch.
The probe checks both ID relationships and exact fictional facts, stopping on the
first failed observation. The fixture ignores the model and cannot prove SDK memory.

Optional --live actually calls Agent SDK query using local authentication and
ANTHROPIC_MODEL. Up to four calls each set2turns/$0.10; SDK budget controls are not
an independently metered billing guarantee. A60second cancellation boundary limits
the probe but process cleanup can take longer. No retries. It may fail if model
output is not the exact JSON contract; that is UNVERIFIED, not permission to loosen
checks. No live run has been recorded for this draft. Without configured access,
complete offline and leave live UNVERIFIED; the website never receives credentials.
SDK may persist fictional transcripts in its local config directory even though
the temporary working directory is removed. Do not delete unrelated sessions.

## Transfer, reset and version boundary

Change the source-version map: explain why a fresh summary is safer than silently
resuming stale results. If only one known file changed and other evidence is valid,
a separate targeted-reanalysis workflow can resume after explicitly naming that
change; this conservative helper intentionally chooses fresh until that workflow
is implemented. For divergent valid analysis, fork history; use separate working
directories/worktrees when real file isolation is needed.

Save your patch, restore only adapter.py from this stage start and rerun. Both
Claude Code/Codex assistance prompts should ask for your prediction, then give one
hint limited to this adapter. Neither assistant's presence proves the SDK probe.
Unread learner execution is self-reported; hints/Reveal never establish mastery.

Guidev1.0 task1.7 is the coverage source. Checked2026-09-20:
https://code.claude.com/docs/en/agent-sdk/sessions . Current Python API uses
ClaudeAgentOptions(resume=ID, fork_session=True); no TypeScript V2 API is used.
Inspect installed0.2.157 options and ResultMessage signatures, rather than replacing
interfaces based on guide CLI terminology. Named Claude Code --resume sessions,
code-exploration scratchpads/manifests and /compact remain separate required labs.
