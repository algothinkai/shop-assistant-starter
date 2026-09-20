# Host review sources — checked2026-09-20

Guidev1.0 tasks3.6/4.6 define noninteractive structured review and independent
contexts. Implementation also practices explicit criteria4.1 and fixed passes1.6.

- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/cli-reference
- https://learn.chatgpt.com/docs/non-interactive-mode

Claude -p uses JSON metadata with structured_output for --json-schema. Current
--bare skips auto project/user context; our prompt supplies guidance explicitly.
Codex exec exposes JSONL terminal events and schema output in the last-message
file. Require successful terminal events and matching final content; output parsing
alone cannot certify review quality. Independent subprocesses omit generator history.

Actual local inspection: SDK bundled Claude Code2.1.277 supports bare/schema/no-tools/
no-session options. PATH Claude --version/--help failed while attempting to write
its user config; no successful PATH version is claimed. Codex0.155.0-alpha.9.2 help
supports the selected exec/schema/read-only/ephemeral/config flags. Neither help
inspection nor authored envelopes is a live model review. Model choice is explicit;
no default/latest model or matching account access is assumed.

Do not confuse the native host CLI, Python Agent SDK and Messages API client SDK.
This adapter invokes a host process; it does not import either SDK. Automatic
CLAUDE.md loading remains a separate required experiment. Saved auth is not copied;
the opt-in example requires a local API key only for the host invocation. A hosted
CI implementation must use its provider's first-party credential guidance rather
than giving untrusted repository steps a job-level key.

Pinned Codex features list confirms the explicitly disabled capability names, including
shell_tool and unified_exec. Read-only sandbox alone would still allow reads; it is
not a no-tools policy. Feature switches are version-specific and actual live tool
availability remains unverified; unsupported flags must fail rather than be removed
silently. No user/global configuration is modified by these command-line overrides.
