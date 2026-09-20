# Stage 6 sources and verification boundary

Coverage: founder-supplied Claude Certified Architect – Foundations Exam Guide
v1.0, tasks1.7/5.1/5.4. This initial local case-state lab addresses part of5.1 only;
metadata for delegated findings and upstream structured responses continue in7.

First-party checked2026-09-20:
- https://code.claude.com/docs/en/agent-sdk/sessions
- https://code.claude.com/docs/en/how-claude-code-works

Current SDK documentation distinguishes continue (most recent), resume (specific
session ID) and fork (new history branch). Conversation persistence does not restore
filesystem changes. Guide names CLI session resumption and fork_session; this lab
implements neither SDK nor CLI behavior. Installed optional Agent SDK remains
0.2.157 from the earlier hook lab, but is not imported here. No dependency changed.
Live SDK/Claude Code/Codex validation is UNVERIFIED and remains later work.

All current checks use Python standard library, fictional local data and authored
conversation. They verify observed persistence/projection behavior, not model memory
quality, token savings, live resumption, or certification readiness.
