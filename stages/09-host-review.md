# Stage 9 — noninteractive host review

Draft tasks3.6,4.1,4.6 and1.6. Start codex/stage-9-host-start, reference
codex/stage-9-host-reference. Keep scripts/test green; scripts/verify-review-host
is the separate exercise. No new Python package is required. Implement context,
command and decode in exercises/review_host/adapter.py; the bounded process helper,
JSON schema and run_pass wrapper are supplied. Prior review aggregator is complete.

## 1. Supply a fresh review context

Predict what a fresh reviewer knows about tests and earlier findings. Build context
from the exact source snapshot, scoped pass, existing test files and optional prior
issue inventory. Include concrete criteria and examples from GUIDANCE; do not send
generator conversation or resume its session. Prior findings are data to reassess,
not proof of a bug. Request only new or still-unaddressed findings, retaining stable
path/symbol/cause anchors. A source line must match exactly; never invent a location.

## 2. Use the correct host contract

Before command construction, explain why the same flags cannot be reused for both
hosts. Claude Code uses --bare -p --output-format json --json-schema, no tools and
no session persistence. Bare skips automatic CLAUDE.md; project guidance is supplied
explicitly in the prompt here. This does not prove automatic CLAUDE.md loading.
Codex uses exec --json --output-schema --output-last-message, read-only sandbox,
ephemeral fresh context and no user config/rules. Known shell, execution, app,
browser, computer, image, code-mode, multi-agent, hook, plugin and dependency
capabilities are explicitly disabled before launch; post-run tool-event rejection
also remains. Unknown future host capabilities still require version review. Both run in a new temporary
working directory with supplied source text. No resume, interactive approval or
repository edit is requested. This is not a claim of fully isolated host state.

## 3. Require completion before accepting findings

Predict the difference between process exit zero, a success terminal event and
valid structured findings. Require all three, then reuse source/location validation.
Claude returns findings under structured_output only after a successful result.
Codex must end one started turn successfully; its last agent message must agree
with the final JSON file. A stale file, missing terminal, nonzero exit, error,
unexpected tool activity or malformed schema is not an empty successful review.
The helper limits duration/output and cleans up owned processes. If group cleanup
is unavailable, report that uncertainty; never silently certify cleanup succeeded.

Run scripts/verify-review-host. Predict, run and compare both authored paths:

```sh
python3 -m exercises.review_host.demo --host claude --all-passes
python3 -m exercises.review_host.demo --host codex --all-passes
```

Authored envelopes deliberately return empty findings. They test plumbing, not bug
recognition; the earlier code fixture still contains its teaching defect. Without
--all-passes only local:refund.py runs, so the aggregate correctly stays incomplete.
Test code also executes small local Python subprocesses for stdin, exit, timeout
and output bounds. Those processes are neither Claude Code nor Codex.

## Explicit live path

Only add --live when you intend to use your local provider account. Set an explicit
SHOP_REVIEW_MODEL plus ANTHROPIC_API_KEY for Claude, or CODEX_API_KEY for Codex, in
that invocation's local environment. Keys never enter the website, prompt or logs.
No .env is auto-loaded. The default live command runs one pass; --all-passes runs
several fresh invocations and may cost more. Claude has a per-call0.50USD budget;
the Codex command does not implement a dollar cap. Both have a120-second local
limit per pass. Do not interpret a timeout as a provider billing guarantee.

Use --executable /absolute/path/to/host when PATH selects an incompatible version.
Inspect host --version/--help first. Missing configuration is UNVERIFIED and starts
no process. PATH Claude may differ from an Agent SDK bundled binary; identify which
one actually ran. The supported source/version ledger is stages/09-host-sources.md.

Optional --prior points to a local JSON issue inventory with revision plus issues,
each containing fingerprint/path/symbol/cause from the preceding aggregate. Review
the new code/tests; not_reobserved still does not mean fixed. This lab uses the
fictional code snapshot, not your working repository. No PR comments or CI workflow
are installed. Do not put provider keys into a job that executes untrusted code.

Original transfer: a host exits zero but refuses the schema request and emits only
plain text. Should the job publish “no bugs”? No: mark the pass failed, preserve
other successful reports, and inspect the host/version/configuration mismatch.
Retry after diagnosing it; do not replace failure with an empty findings array.

Save edits before restoring only adapter.py from the start. Temporary process files
are removed after a run; keep nonsecret summary evidence before resetting. Do not
copy host auth files into artifacts. Claude Code/Codex learner prompt: "Ask me to
predict the terminal evidence, then help only this function or failure with one
hint." Manual editing uses the same tests. Unread local reports remain self-reported.

Still required: actual live passes on both hosts, project CLAUDE.md loading lab,
CI fixture-run configuration, representative quality calibration and guided DAG.
