"""Learner recovery coordinator; imports only explicit recorded task exports."""
from .artifacts import TASKS, read_bytes, digest, parse


def manifest(exports):
    raise NotImplementedError("Index explicit completed exports and missing work")


def recover(root, directory, index):
    raise NotImplementedError("Recheck export/source integrity and retain only fresh findings")


def next_prompt(recovered, question):
    raise NotImplementedError("Inject fresh findings and unresolved tasks into the next phase")
