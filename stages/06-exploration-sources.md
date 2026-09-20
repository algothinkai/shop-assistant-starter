# Exploration source ledger — checked 2026-09-20

Coverage: Exam Guide v1.0 tasks1.7 and5.4. The fixed local structural scan is only
an engineering harness. It does not prove model subagent, compaction or CLI resume.

First-party sources:
- https://code.claude.com/docs/en/sessions : explicit names and IDs, /rename and
  named --resume; picker and SDK histories are different paths.
- https://code.claude.com/docs/en/commands : /compact accepts optional focus text.
- https://code.claude.com/docs/en/common-workflows : scoped research delegation and
  separate worktrees for concurrent file edits.
- https://learn.chatgpt.com/guides/best-practices : Codex CLI /resume, /fork,
  /compact and bounded subagent exploration.

Current guide terminology remains applicable, but actual installed capabilities
must be checked. This author environment returned codex-cli0.155.0-alpha.9.2 from
--version; the PATH claude command exited1 without a usable version. Neither
interactive named-session/compaction experiment ran. Earlier pinned SDK0.2.157
uses its own bundled CLI; do not treat that as proof this PATH CLI works.
No tool upgrade/configuration changes were made. Recovery: manual lab with explicit
UNVERIFIED host evidence, then rerun the host-specific experiment when available.
