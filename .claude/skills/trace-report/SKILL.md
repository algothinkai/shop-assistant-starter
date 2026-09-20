---
name: trace-report
description: Trace the Stage 1 report call chain after the learner has predicted its path.
argument-hint: "<symbol and predicted caller>"
disable-model-invocation: true
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

Analyze only exercises/collaboration and shop_assistant/business.py.
Input: $ARGUMENTS. If the symbol or predicted caller is missing, return a request
for it and stop. Locate paths, search exported symbols and read callers. Return
at most five path/symbol findings and one uncertainty. No edits, shell commands,
solution patches or future-stage exploration. Do not assume parent conversation
context: the request must include the prediction and scope.
