# Review source ledger — checked 2026-09-20

Coverage source: founder Exam Guide v1.0 tasks1.6,3.6,4.1,4.6; few-shot technique
also relates to4.2 but this slice does not claim its full extraction-focused skills.
Current first-party interfaces:

- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/cli-reference

Guide flags -p, --output-format json and --json-schema remain documented. Current
JSON output places schema-conforming results in structured_output; process/terminal
failure must not be treated as empty findings. Current docs additionally recommend
--bare for scripted calls; it skips automatic CLAUDE.md, settings/hooks and other
host context. Thus a bare call must explicitly supply required project guidance;
a separate non-bare project-context experiment is needed to teach CLAUDE.md loading.
Do not silently substitute one behavior for the other. No actual host invocation,
CI job, account access, structured output or Codex equivalent is verified here.
The implementation is a Python local aggregator with authored reports, not Agent
SDK, Messages client SDK or a working CI integration.
