# Batch source ledger — checked 2026-09-20

Coverage source: founder Exam Guide v1.0 task4.5. Current interface sources:

- https://platform.claude.com/docs/en/build-with-claude/batch-processing
- https://platform.claude.com/docs/en/api/messages/batches/create
- https://platform.claude.com/docs/en/api/messages/batches/results

The guide's24-hour window is an expiry/planning boundary, not a successful-delivery
SLA. Current docs retain asynchronous processing and discounted model usage.
No exact model price or measured savings is claimed in this local lab.

Guide says no mid-request tool execution/return: this remains a boundary for local
client tools. Current docs additionally support server tools and server-side loops;
do not teach a universal ban on all tool use. This lab's extract_receipt tool call
is structured data, then locally validated. It neither executes shop functions nor
continues an interactive tool loop inside the batch. pause_turn/truncation cannot
be accepted as complete extraction.

Create uses POST /v1/messages/batches with requests containing unique custom_id
and standard Message params. Results use GET /v1/messages/batches/{id}/results,
JSONL, arbitrary order and succeeded/errored/canceled/expired outcomes. The local
20-document/500KB caps are teaching limits, not vendor limits. No API SDK upgrade,
actual submission, billing result or production deployment is claimed.

Lifecycle extension: GET /v1/messages/batches/{id} is the idempotent status
operation (https://platform.claude.com/docs/en/api/messages/batches/retrieve).
Persist ID and request counts; status is in_progress, canceling or ended.
This lab uses the documented fixed results endpoint instead of following arbitrary
results_url values, has no automatic POST retry, and records uncertain creation.
The transport is Python standard-library HTTPS with anthropic-version2023-06-01;
no Messages client SDK or Agent SDK runs this lifecycle. Local authored transport
checks do not establish provider acceptance, timing, pricing or model quality.
