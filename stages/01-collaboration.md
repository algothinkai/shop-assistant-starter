# Stage 1 — Make a report you can trust

Draft teaching stage. Start on `codex/stage-1-start`; reference answers are on
`codex/stage-1-reference`. Neither replaces the Stage 0 baseline branch. Complete
one checkpoint at a time; the algothink course supplies questions and feedback.
No model or paid credential is required for the Python repair. Tool-specific
experiments need the corresponding installed, authenticated tool; mark them
UNVERIFIED when unavailable. Never paste credentials or personal config content.

## A. Locate before editing (10 minutes)

Goal: explain which function turns shop events into a report. Predict the caller
of `summarize_run` before searching. Find paths with `rg --files exercises`; search
content with `rg -n 'summarize_run|case_report' exercises`, then read just the
matched files and the `events` function in `shop_assistant/business.py`. In Claude
Code use Glob for paths, Grep for content and Read for the identified files.
Trace the exported wrapper as well as its import: finding the definition is not
finding every caller. Record paths and a three-arrow data flow.

Run `scripts/test` and `scripts/verify-stage 0`; both should pass. Predict the
Stage 1 check result, then run `scripts/verify-stage 1`. Failures here are the
exercise, not a broken installation. Save a failing assertion, actual and expected
values. A result event is not the terminal case outcome. Do not edit yet.

Recovery: rerun the baseline from the repository root. If search is empty, check
your working directory and spelling; do not load the entire repository at once.

## B. Put instructions where they belong (15 minutes)

Before changing any file, classify: team invariant, personal response preference,
cross-directory test convention, one-off investigation. Predict which a teammate
will receive from Git. Inspect root CLAUDE.md, exercises/collaboration/CLAUDE.md,
its @import and .claude/rules/collaboration-tests.md. The guide names /memory;
current /memory lists configuration locations, including absent files. Use
/context to inspect actual loaded instructions: record a fresh session before
and after reading checks.py. In a separate fresh session read only report.py as
a nonmatching control, so an already-loaded test rule cannot contaminate it.
Do not treat the model saying it obeyed as proof. Record installed version and observable tool
messages, including missing features. Do not edit global personal files for this
lab: sketch a personal preference and explain why it should stay uncommitted.

After predicting the call chain, invoke `/trace-report summarize_run; predicted
caller=case_report` if your Claude Code supports this skill. Inspect its short
findings against A. Its fork gets explicit inputs; do not assume it inherits your
conversation. Read frontmatter: argument-hint guides invocation, context: fork
isolates exploration, and allowed-tools is not a security sandbox. Keep normal
permission restrictions; our instructions explicitly prohibit edits. For the
legacy-command comparison, sketch .claude/commands/trace-report.md without
installing a competing command. For a personal variant, choose a different name.

Codex path: open Codex from exercises/collaboration so its nested AGENTS.md is in
the instruction chain. Read the referenced standard explicitly and ask for the
same bounded search. This is not the Claude /context, glob-rule or forked-skill
experiment. Record the Codex version and observations separately. If either tool
is unavailable, perform the searches in a terminal and retain UNVERIFIED for that
tool-specific checkpoint. Nothing in a Python PASS certifies tool loading.

Recovery: undo only your own experimental files after inspecting git diff; leave
home configuration untouched. Restart a session after changing instruction files.

## C. Repair with evidence (15 minutes)

Goal: report one run accurately. Allowed implementation changes: only
exercises/collaboration/report.py. You may add a regression in checks.py without
removing or weakening existing cases. Keep UI, business fixtures and future stages
unchanged. First decide whether this bounded defect needs direct execution or a
plan. Ask the assistant to interview you about an incomplete run before editing.
Give concrete examples: A has two calls and a completed outcome; B has one call,
one error and blocked outcome; C has a successful result but no outcome and is
incomplete. The event log is ordered and trusted local data; do not add a generic
network event ingestion service.

Use the failing check to guide the smallest change. An ambiguous Edit anchor is
not permission to replace all matches: read the full small file, then make a
precise edit or a reviewed full-file Write. Inspect the diff and run
`scripts/verify-stage 1`, then `scripts/test` and `scripts/verify-stage 0`.
Expected after repair: all five exercise checks and the baseline pass. Save the
before/after assertions and explain why a different run cannot affect this one.
Transfer: imagine report logic moving into three packages with different event
schemas. Decide what would justify plan mode and an isolated Explore investigation
before implementation. Group interacting schema issues; handle an unrelated copy
change separately. Reading a reference is assisted, not demonstrated.

Recovery: save your patch with `git diff > ../stage1-work.patch`; inspect git
status. To reset only the exercise implementation, use
`git restore --source=codex/stage-1-start -- exercises/collaboration/report.py`
after saving your work. `scripts/reset` resets shop state, not exercise code.
To compare the reference, use a separate worktree rather than overwrite your work:
`git worktree add ../shop-stage1-reference codex/stage-1-reference`.

Suggested assistant prompt: “Checkpoint C only. Ask for my method, expected
failure and why before editing. Wait. Then help repair only report.py using the
real failure output. Show the diff and actual test results; don't do my transfer
question or open reference answers.”

## Sources and verification boundary

Exam Guide v1.0: 2.5 and 3.1–3.5. Current sources checked 2026-09-20:
[Claude memory](https://code.claude.com/docs/en/memory),
[Claude skills](https://code.claude.com/docs/en/skills),
[Claude workflow](https://code.claude.com/docs/en/best-practices),
[Codex instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
Guide/current distinctions: /memory lists locations, while /context shows loaded
instructions; current path rules can load on reading matching files;
custom commands are now part of skills while legacy command files remain supported;
allowed-tools is an auto-approval list, not a replacement for permission controls;
a forked skill does not inherit conversation history. Inspect your installed
version before assuming these current features. The previously observed local
Claude 1.0.17 is older; no live skill/rule/plan behavior is certified here.
