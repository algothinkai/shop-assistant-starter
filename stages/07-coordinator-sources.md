# Source and interface ledger — checked 2026-09-20

Coverage source: founder-supplied Claude Certified Architect – Foundations Exam
Guide v1.0, tasks1.2/1.3/1.6/5.3/5.6; guide hash is in algothink's manifest.

- https://code.claude.com/docs/en/agent-sdk/subagents
- https://code.claude.com/docs/en/agent-sdk/python
- https://code.claude.com/docs/en/agent-sdk/custom-tools

Implementation pins existing Python Agent SDK0.2.157. Local signature inspection
confirms AgentDefinition, PreToolUse agent_type/agent_id, updatedInput, options,
and actual SDK MCP registration. SDK client options are not a live run.
Guide calls the delegation tool Task; current docs call it Agent, with older or
init events sometimes Task. Configure Agent and observe both names. Guide isolated
context applies to these non-fork agents; current forks have different inheritance.
Background defaults changed: this exercise explicitly sets run_in_background=false.
The documented depth/concurrency/budget controls require current bundled CLI; live
behavior still needs verification. No unpinned interface or older guide spelling
is silently substituted. This is Agent SDK, not the Messages API client SDK.
