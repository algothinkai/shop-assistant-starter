# Stage 4 extension — Agent SDK hooks (draft)

Learning start: codex/stage-4-hooks-start, based on the after-sales reference.
The separate codex/stage-4-hooks-reference contains completed callbacks. Edit only
`exercises/agent_hooks/callbacks.py`. Keep the core workflow guards and checks.

## Setup and evidence boundary

```sh
scripts/setup-agent
scripts/verify-hooks
.venv-agent/bin/python -m exercises.agent_hooks.demo
```

The optional `.venv-agent` pins Claude Agent SDK 0.2.157 and dependencies. It is
separate from Stage 3's `.venv`; the baseline still needs neither. Start callback
checks intentionally raise NotImplementedError until implemented. Baseline and
Stage 4 workflow checks still pass. The default demo directly invokes callbacks
registered in real SDK options; it does not start an agent or call a model.

## 1. Block the request before execution

The agent asks to refund O-1003, but local simulated identity is unverified.
Choose a prompt reminder or a programmatic precondition and explain what failure
you need to prevent. Predict the hook decision and ledger before implementing it.

Implement the PreToolUse callback for the exact registered refund tool. Reject
invalid amounts, another order and unverified/unavailable local identity. This
experiment also uses a clearly labeled $500 teaching ceiling; it is an additional
lab guard, not a newly approved store policy. Above it, deny and recommend human
review; never divide the amount to evade it. The existing workflow/atomic business
guards still apply if preflight passes. Returning {} continues normal permission
checks; it does not independently approve the tool or record a refund.

Hints: inspect the registered full MCP tool name; then inspect permissionDecision
and its reason. Do not use background/async hook output for a decision that must
precede execution. Run scripts/verify-hooks and inspect the denied cases, identity
revocation and empty ledger. Transfer: the prompt says an urgent exception is fine.
Explain why the deterministic rule still applies and what a human needs to decide.

## 2. Normalize a successful result before model use

Two authored carrier fixtures encode the same instant and delivery state: Unix
seconds/status code 20 and an ISO timestamp with offset/status delivered. Predict
one canonical UTC result. Implement PostToolUse transformation for shipping_sample,
using updatedToolOutput, retaining the fictional-source label and original input.
Do not assume a timezone for an unqualified timestamp or guess an unknown status.
Preserve existing tool errors; invalid data becomes an explicit normalization error.

Hints: separate parsing from semantic status validation; compare the two canonical
outputs and then try missing timezone, Boolean timestamp and unknown numeric code.
Inspect the replacement output and audit event. Transfer: the carrier tool fails.
An output transformation cannot turn that failure into a successful delivery.

## 3. Separate a callback check from an actual SDK run

The adapter creates two scoped SDK MCP tools and registers exact hook matchers.
Built-in tools and user/project settings are disabled for this isolated experiment.
The SDK runtime is different from the raw Messages API loop and from using Claude
Code or Codex as an editor. Either coding assistant can help with this checkpoint:
ask for a method/prediction first, offer one hint, and restrict edits to callbacks.py.
Success in that editing tool does not prove live runtime behavior.

If you deliberately want a billable local experiment, authenticate locally through
the SDK's supported path, set ANTHROPIC_MODEL to a model you can access, and run:

```sh
.venv-agent/bin/python -m exercises.agent_hooks.demo --live
```

The run requests a carrier sample and an unverified refund. Limits: four turns,
$0.10 SDK budget, 60-second timeout. No identity-setting tool is exposed. Inspect
actual hook events: normalized PostToolUse and denied PreToolUse, plus empty ledger.
If either event is absent, status is UNVERIFIED even if a response was generated.
OBSERVED_REQUESTED_HOOKS proves those callbacks ran, not every possible workflow or
that all course skills are mastered. A later runtime error is not a passing full
integration test. The demo prints event/type summaries, never credentials or raw
exception messages. No live run was made during this draft's engineering checks.

If access is unavailable, retain OFFLINE_ONLY results and resume the live check
later. Never relabel a callback fixture as captured model behavior. Local notes
submitted to algothink remain self-reported; the website does not read the run.

## Recovery and source versions

Save your patch; restore callbacks.py from the exact start commit if needed.
Each demo creates temporary state. Remove only this optional environment to rebuild
its pinned dependencies; leave Stage 0/3 environments and personal settings alone.
No host hook installation or global configuration change is part of setup.

Guide v1.0 task 1.5 motivates this lab, alongside 1.4/5.2. Current first-party
[SDK hook docs](https://code.claude.com/docs/en/agent-sdk/hooks) and
[Python reference](https://code.claude.com/docs/en/agent-sdk/python) were checked
2026-09-20. Installed Python SDK 0.2.157 exposes updatedToolOutput; the older
updatedMCPToolOutput is deprecated. The guide describes the transformation goal,
not this current field spelling. Keep implementation version and coverage source
separate. Multi-concern work, intent/few-shot exercises and the main-site Module 4
DAG are still pending. Curriculum publication requires founder approval.
