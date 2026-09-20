# Stage 8 — reconstruct a split receipt for review

Draft task4.5 extension. Start `codex/stage-8-reconstruction-start`, reference
`codex/stage-8-reconstruction-reference`. The start inherits completed local batch
and lifecycle code. It leaves only exercises/batch_reconstruction/merge.py unfinished.
Use scripts/setup-agent if needed. Foundation scripts/test stays green; explicit
scripts/verify-batch-reconstruction fails until this exercise is implemented.

A chunk is one part of the original text. Lineage records its parent receipt and
position. Earlier retry planning requires exact source-preserving partitions.
Now decide whether individually plausible fields can form one defensible receipt.

Before editing, predict these three outcomes: fields occur in complementary parts;
two parts each contain a different order ID; one part expired. Explain why choosing
the last value or accepting the successful half would lose evidence.

Implement reconstruct only. Recompute the retry plan from the parent manifest,
original results and explicit partitions; never trust a caller-edited lineage map.
Use the existing JSONL importer to bind every retry ID. Reject missing, duplicate
and unknown results. Keep all field-level child/source-part evidence. A null in one
part can coexist with a supported value in another; a field invented from a sibling
part is invalid in the local part. Retain conflicts and failed chunks. If compatible,
validate the reconstructed proposal against the complete original source again.
Even a valid proposal is ready_for_review, never accepted automatically.

Run scripts/verify-batch-reconstruction. Compare complementary versus conflicting
field evidence, whole-source missing fields, expired children and preserved valid
parent receipts. Run .venv-agent/bin/python -m exercises.batch_reconstruction.demo
for an authored complementary example. No provider/model calls occur.

Hints: first distinguish absent information from wrong evidence; then group only
validated non-null fields by parent and field; finally revisit the original source
so cross-part contradictions cannot vanish. Compare your attempt with only merge.py
in the reference after recording predictions. Passing chunks alone are insufficient.

Original transfer: two pages both contain the same supported order ID. Is this a
conflict? No, retain both supporting entries. Different normalized values would be
a conflict; repeated agreement does not fill an unrelated missing customer field.
A smaller chunk can split a labeled line or needed context; choose a better explicit
partition and re-extract rather than guessing the missing fragment.

Save your patch before restoring only merge.py from the start. This in-memory lab
has no state to reset and no ledger effects. Existing live batch files must not be
deleted for this exercise. Claude Code/Codex prompt: "Ask for my merge prediction
and reason, then give one hint for the current failing case. Do not implement the
whole module." Manual editing uses the same checks. Local unread logs remain
self-reported; Reveal does not demonstrate mastery. Provenance is caller supplied,
so neither this report nor fixtures prove live model quality or publication approval.
