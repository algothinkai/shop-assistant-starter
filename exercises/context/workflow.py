"""Learner exercise: exact observations before compressed narrative."""
from copy import deepcopy
import json
from .state import validate, versions, read_snapshot


def record_fact(state, issue_id, field, value, source, observed_at):
    raise NotImplementedError("Preserve issue-scoped observations and conflicts")


def trim_order(result):
    raise NotImplementedError("Keep relevant fields and explicit errors")


def build_context(state, history, summary):
    raise NotImplementedError("Keep exact case facts separate from full history")


def recover(path, current_versions):
    raise NotImplementedError("Compare source versions before reusing case facts")
