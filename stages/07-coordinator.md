# Stage 7 — adaptive SDK coordinator (draft)

Start: codex/stage-7-coordinator-start. Reference: codex/stage-7-coordinator-reference.
Use scripts/setup-agent for the existing pinned Python Agent SDK0.2.157 environment.
The local foundation remains scripts/test; scripts/verify-coordinator is the explicit
unfinished exercise. Edit only exercises/coordinator/adapter.py. Earlier synthesis
and the read-only fictional source service are supplied and reused.

## Choose, explain and predict

A customer asks about shipping only. Should every specialist run? Explain why
scope follows the question, then predict which agent/tool events should be absent.
For a request covering returns and shipping, identify independent work that can
share a coordinator turn. A subagent is a separate agent conversation: give it the
question, policy date, allowed sources, full relevant earlier findings and gaps.
It must not rely on the parent's conversation appearing automatically.

## Practice

Configure AgentDefinition instances for requested topics. Limit each to the
investigate tool; only the coordinator can delegate and inspect_coverage. Enforce
roles and source scope in a PreToolUse hook. At delegation, keep the model's goal
but inject explicit dated context and complete prior topic evidence. Require
foreground results (run_in_background=false); independent Agent calls can still
be in one response. This makes result collection explicit without assuming the
current background-default behavior.

The coordinator prompt specifies goals/quality, not a fixed call pipeline: choose
relevant agents, partition topics, inspect reports, re-delegate missing or failed
sources, preserve healthy work, and stop with attributed uncertainty when conflict
or exhaustion remains. Local source retrieval retries a transient timeout once;
unresolved failure propagates with partial findings and alternatives. Retrying a
real policy disagreement until it disappears is not recovery.

Implement consume to require observed Agent/Task calls, associated child tool use
and results, registered delegation context, current coverage inspection and one
successful terminal SDK result. Text saying "done" is insufficient. Error, budget
limit, missing terminal, stream exception or unrelated child events must remain
unverified. A verified workflow can still have contested or partial coverage.

Run scripts/verify-coordinator. Then:

    .venv-agent/bin/python -m exercises.coordinator.demo
    .venv-agent/bin/python -m exercises.coordinator.demo --topics shipping
    .venv-agent/bin/python -m exercises.coordinator.demo --fault transient
    .venv-agent/bin/python -m exercises.coordinator.demo --fault persistent

Default runs have authored SDK messages but execute the registered local tool
handlers and real guards. They cannot prove model-driven selection, SDK dispatch,
parallel execution, or Claude Code behavior. Inspect events: first returns report
has a gap; follow-up only revisits returns; source dates/conflicts survive.

For a real opt-in run, set ANTHROPIC_MODEL locally, configure your existing Agent
SDK credentials locally, and add --live. No website receives credentials. The
query has a $0.50 SDK budget cap,16-turn cap,120-second timeout, depth1/concurrency2
limits, no filesystem/shell tools, no project settings, no refund tools. Limits
are failure boundaries, not success conditions. Record actual SDK/model versions,
delegation inputs, child events, local attempts, final coverage and terminal state.
Do not label offline results live when credentials or the host are unavailable.

## Inspect, transfer, recover

Compare shipping-only, missing FAQ, transient timeout, persistent failure and
current-policy conflict. Explain when local retry, targeted re-delegation or human
policy review is appropriate. Change topic requirements and predict delegation.
A single response containing two Agent calls proves requested parallel work, not
measured simultaneous execution. Source coverage is limited to the known corpus.

Save your patch before restoring adapter.py from the start ref. No ledger reset is
needed. Without SDK/model access, run offline checks and mark live work UNVERIFIED.
Claude Code/Codex prompts: "Ask for my topic partition and predicted events first;
help only the current adapter function and one failing case, not the entire lesson."
Using Codex to edit this Python program does not verify Claude Code's own workflow.
Unread learner evidence is self-reported; Hint/Reveal never demonstrate mastery.
