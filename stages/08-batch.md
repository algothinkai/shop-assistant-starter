# Stage 8 — overnight receipt batch (partial draft)

Start codex/stage-8-start; reference codex/stage-8-reference. Reuse the existing
Module5 Messages extraction request and local source validator. The Messages API
and its batch endpoint are distinct from Agent SDK. No new business system or
refund action is introduced. This lab is local; it does not submit actual batches.

## Choose, explain, predict

The shop needs a later audit of receipts, while a customer in chat needs an answer
now. Explain which can tolerate queue time. Add submission cadence, a24-hour
processing assumption and recovery margin. A30-hour deadline with4-hour cadence
and2-hour recovery fits that planning calculation, but expiry/failure still means
there is no guaranteed completion SLA. A blocking request or local tool round-trip
requires an appropriate synchronous workflow, not a cheap batch with a timer.

## Practice

Run scripts/setup-agent if the existing jsonschema environment is absent. The
foundation is scripts/test. Edit only exercises/batch/workflow.py; dedicated
scripts/verify-batch checks remain intentionally unfinished at the start.

1. Implement schedule with explicit assumptions and no completion guarantee.
2. Implement reconcile: require ended status, match JSONL records by custom_id,
   reject duplicate/unknown IDs and ambiguous JSON, preserve missing records. A
   provider succeeded response still needs extraction terminal and source checks.
3. Implement scale_up: compare the exact model, prompt note, source documents and
   bound payload; two sample documents must validate before preparing remaining
   work. Do not resubmit already validated sample IDs. Source validation on this
   small labeled corpus is not representative model-quality measurement.
4. Implement retry_plan: retain successes; retry transient/expired items, hold
   cancellation, bad requests and invalid extraction for review. For a confirmed
   context-size problem, caller-supplied chunks must partition the entire failed
   source exactly, retain parent lineage and require new sample/merge review.
   Do not assume every invalid_request_error means context length. Chunking a
   receipt may separate required fields, so no automatic merged success is claimed.

Predict outcomes before scripts/verify-batch and:

    .venv-agent/bin/python -m exercises.batch.demo --scenario sample
    .venv-agent/bin/python -m exercises.batch.demo --scenario mixed
    .venv-agent/bin/python -m exercises.batch.demo --scenario chunk
    .venv-agent/bin/python -m exercises.batch.demo --scenario missing

Inspect actual request/manifest hashes, result IDs, cents/evidence, remaining IDs,
retry lineage and review flags. The sample scenario changes authored candidate
records: it demonstrates a quality gate, not real prompt improvement. A later live
experiment must refine prompts on representative samples and retain its evidence
before submission. Current modes retain caller-supplied provenance, never certify
that a model produced a manually supplied result.

## Transfer and recovery

Reverse result order and predict whether the receipt amounts move to wrong IDs.
Change only the prompt/model after sampling: explain why the earlier gate no longer
applies. Cancel one item and explain why automatic retry would ignore intent.
Lose a result line and explain why resubmitting it before complete retrieval can
repeat successful work. Shorten the deadline and calculate whether cadence alone
can make the plan fit; do not interpret expiry as guaranteed successful processing.

Save your patch before restoring workflow.py from the start. Demo state is in
memory; no ledger/key/network is involved. Claude Code/Codex prompt: “Ask for my
prediction and reason, then help one current function or failing case; do not solve
the entire stage.” Manual editing follows identical checks. Unread local evidence
is self-reported; Hint/Reveal is not demonstrated mastery. Actual API create/poll/
results lifecycle and representative live prompt refinement remain unverified.
