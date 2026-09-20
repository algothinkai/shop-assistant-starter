# Stage 8 — resume one batch safely

Draft, objective 4.5. Start: `codex/stage-8-lifecycle-start`; reference:
`codex/stage-8-lifecycle-reference`. Builds on the completed local batch lab.
Use the existing pinned `.venv-agent` (`scripts/setup-agent` if needed).
Foundation `scripts/test` stays green. `scripts/verify-batch-lifecycle` is an
explicit exercise and fails until its three lifecycle functions are implemented.
No website collects keys. All receipts are fictional. No refund/payment occurs.

A batch is a provider job that can outlive this terminal. A manifest binds its
exact input, model and prompt. Provider completion and correct extraction are
separate facts. This lab reuses the earlier receipt validator and batch importer.

## 1. Submit once, then lose the connection

Choose: should a POST timeout automatically trigger another POST? Explain whether
you know that the first request failed to create a job. Predict how many jobs two
concurrent submit commands should create. Implement `submit` in
`exercises/batch_lifecycle/lifecycle.py`: validate the payload, lock the local
store, write unknown intent durably before POST, bind returned ID and counts.
An existing known job returns its saved state; unknown submission fails closed.
Hint 1: a timeout can happen after the server accepted work. Hint 2: the marker
must survive a crash before you can save the returned ID. Reveal: inspect only
this function in the separate reference after recording your prediction.

## 2. Restart without submitting

Predict the network methods needed after closing the terminal. Implement `refresh`
and `collect` in the same file. Retrieve only the saved provider ID. Require ended
status, exact custom IDs and outcome counts before saving results. Use the fixed
results endpoint, never a provider-supplied URL. Revalidate cached content on read.
Hints: missing JSONL records are not permission to resubmit; provider success still
needs receipt/source validation. A collected job can contain items needing review.

Run each command as a separate process; default mode is authored, no network:

```sh
.venv-agent/bin/python -m exercises.batch_lifecycle.demo sample --job .local/lab8.json
.venv-agent/bin/python -m exercises.batch_lifecycle.demo status --job .local/lab8.json
.venv-agent/bin/python -m exercises.batch_lifecycle.demo collect --job .local/lab8.json
scripts/verify-batch-lifecycle
```

Expected methods: POST, GET, GET_RESULTS; statuses submitted, ended, collected.
Repeating sample/collect for the same job causes no second POST/download. Inspect
both the saved manifest and actual printed call log. Checks also start a separate
Python process and verify GET-only recovery, concurrent submission, unknown state,
wrong provider ID/counts, incomplete results and cached-result tampering.

Original transfer exercise: the provider completed two requests but one extraction
contradicts its receipt. Is the batch collected, and should both requests be sent
again? Answer: complete transport results may be collected while one item needs
review/repair. Keep the valid item; inspect the failed item's cause before a new
explicit retry plan. Confusing API success with source correctness loses evidence.

## Live path and recovery

Opt-in commands add `--live` and a separate `--job .local/live-sample.json`.
Set `ANTHROPIC_MODEL` and `ANTHROPIC_API_KEY` only in the local shell; do not paste
keys into this site, Git or evidence logs. Sample sends exactly two fictional
receipts and can incur API charges. No bulk submission or automatic polling is
implemented. Run status later; collect only when ended. Missing configuration is
UNVERIFIED, never a passed live check. The `.env` file is not loaded automatically.

Never delete/reset a live unknown job to “try again”: it may already exist and
be billable. Preserve its manifest, inspect your provider account/request records,
and resolve whether a job was created before deliberately making another request.
This lab intentionally has no guessed-ID adoption or automatic unknown retry.
A corrupt file also needs investigation; do not silently overwrite it. A failed
GET or incomplete download preserves state and can be retried for that same ID.

For an authored reset only, choose a new unused `.local/` filename. To restore the
exercise without losing work, save your edits first, then restore only lifecycle.py
from the start ref; do not reset the whole repository. Reference comparison uses
`git show codex/stage-8-lifecycle-reference:exercises/batch_lifecycle/lifecycle.py`.

Claude Code and Codex share this lab prompt: “Ask me to predict the next network
method and justify safe recovery. Help only the current lifecycle function;
inspect its failing check, offer one hint, and do not complete the later checkpoint.”
These commands exercise Python/API behavior, not host-specific Claude Code behavior.
Local logs not actually read by algothink remain self-reported learning evidence.
