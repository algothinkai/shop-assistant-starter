# Stage 6 extension — exploration notes that survive a restart (draft)

Start codex/stage-6-exploration-start; reference codex/stage-6-exploration-reference.
Use Python standard library. Edit only manifest, recover and next_prompt in
exercises/exploration/workflow.py. Foundation scripts/test stays green; separate
scripts/verify-exploration intentionally fails until this exercise is implemented.

## Choose, explain, predict

Two bounded questions need investigation: locate refund-named definitions in
shop_assistant/business.py and refund-named tests in tests/test_baseline.py.
Separate investigators can keep verbose exploration away from the coordinator.
A scratchpad is a durable note of findings, sources and unknowns, not a replacement
for checking code. Predict what a restart loses without a manifest of saved work.

The supplied scanner uses AST (Python syntax structure) in two independent local
processes. It locates matching definitions and quotes their exact source lines.
It is not an AI agent, full dependency tracer or exhaustive repository inventory.
The method, observation date and full-file hash are saved in immutable JSON exports.
Actual model subagents use the separate host experiment below; local workers do
not count as live agent execution. Never label name matches as passing tests or
complete runtime-flow knowledge.

## Implement and inspect

manifest receives an explicit map of task IDs to completed export entries, each
with file and sha256. Include both known task IDs, using None for missing work;
version=1. Validate exact content-addressed filenames and hashes; do not discover
arbitrary old files in the output directory. The coordinator controls which task
run belongs to this phase. No export is assumed complete merely because it exists.

recover loads only indexed exports. Check immutable bytes, expected task/source,
method/metadata, nonempty findings and source-line quotes. Rehash the current source;
changed, missing, corrupt or mismatched evidence requires that task to rerun. Keep
independent fresh tasks, rather than erase all progress. Return status ready only
when both tasks have reusable structural findings; otherwise partial, with fresh
and rerun fields. Ready is not proof of complete program analysis or safe refunds.

next_prompt places fresh findings with file:line citations first, followed by
unknowns and missing/stale task IDs, then the next question. Reject invalid state or
oversized context instead of silently dropping caveats. This is an explicit input
for a subsequent investigator, not an already-executed model prompt.

Run scripts/verify-exploration; predict python3 -m exercises.exploration.demo
--scenario fresh. Repeat changed, interrupted and corrupt. The demo copies only the
two source files into a temporary tree, runs two actual worker processes (one for
interrupted), writes a manifest and starts a NEW recovery process reading that file.
changed mutates only the temporary business.py; only refund-code should rerun.
corrupt damages that task export; the independent tests finding stays available.
Inspect worker events, sources and next_prompt. No business data or ledger is edited.

## Real host experiment — separate unverified evidence

Before a live run record tool version and local access. These actions may use your
account; no key is sent to the website. Work in a disposable checkout or save your
patch first. The following is a learner-driven experiment, not something the local
scanner proves has happened.

Ask your host: “First ask which question I would isolate and why. Then delegate
only locating refund definitions in business.py and locating refund tests in
test_baseline.py to two read-only subagents. Each returns paths/lines, source version,
observation time, method limits and unresolved questions. Do not edit project code.
Save each finding to a separate scratchpad under .local/exploration-notes; keep a
manifest of task status and files. Do not implement later checkpoints.”

After reading the notes, summarize the confirmed findings and gaps before the next
phase. Ask a follow-up investigator to read that summary and inspect ONLY the known
refund function plus the named tests; compare whether the citations support its
claims. Stop the host, restart, load the manifest and reread changed files. On a
throwaway copy add a comment to business.py; tell the resumed session exactly which
file changed and require targeted reanalysis. If broader assumptions are stale,
start fresh with a checked summary. Record actual tool events and unresolved gaps.

Claude Code path: /rename shop-refund-exploration, exit normally, then
claude --resume shop-refund-exploration. Verify the selected session, do not use an
ambiguous name blindly. Before /compact, save the scratchpad, file versions and
open questions; run /compact Preserve exact file paths, source versions and unresolved questions.
Ask the same specific follow-up afterward and compare citations against files.
Successful command execution alone does not prove no information was lost.

Codex CLI path: use /resume to select the intended saved chat; /fork only when
exploring a divergent approach; /compact for a shorter context. Reload the same
scratchpad and repeat the citation comparison. These operations do not validate
Claude Code commands. Keep both evidence records separate. No application settings,
approval permissions or global hooks need changing for this lab.

If the host, access or a feature is unavailable, perform the manual structural
experiment, retain exports, mark that host experiment UNVERIFIED and return later.
Do not substitute worker output for a live subagent or compaction result. Guide1.7
and5.4 need these observations plus teaching/transfer evidence before full coverage.

## Recovery and transfer

Save your patch and restore only workflow.py from this stage start. Demos remove
their temporary tree automatically; keep your own notes if doing the host exercise.
A branch of conversation does not isolate code files. Use separate working copies
when two alternative implementations could edit the same source. Change one source
and explain why only its dependent export is stale; then add another untracked
module and explain why the fixed two-file investigation does not cover it.

Default checks are local, deterministic and no-model. Unread learner runs are
self-reported; hints/Reveal never demonstrate mastery. Source/version notes are in
06-exploration-sources.md. Full model-agent orchestration continues in Module7.
