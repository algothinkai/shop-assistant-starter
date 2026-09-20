# Messages extraction source ledger

Coverage source remains Exam Guide v1.0, tasks4.3/4.4. Checked 2026-09-20:

- https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
  documents tool_choice; forced choice is not supported by every model/setting.
  Unlike a universal reading of the guide, the implementation requires compatible
  user-selected capability and fails on unsupported requests, with no auto fallback.
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
  is the current strict-tool reference. We set strict:true on the extraction tool.
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
  distinguishes strict tools from output_config.format JSON text. We use tool input,
  not the latter. Our nullable schema uses required keys/additionalProperties:false;
  local validation remains necessary for source meaning and protocol failures.

Implementation: raw Messages HTTPS v1 endpoint, anthropic-version2023-06-01,
Python standard library plus the already pinned jsonschema validator. No new SDK
version, model default or live compatibility claim. Model comes from the local
ANTHROPIC_MODEL setting. Record its exact value and actual run separately before
claiming live verification; never record its key. API client SDK, Agent SDK and
Claude Code are distinct; this exercise is the hand-written API path.

Pending: multi-schema any selection, enrichment ordering, varied-format few-shot,
category handling, actual field-confidence generation and representative live evals.
