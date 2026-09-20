"""Implement one durable batch job without automatically replaying submission."""


def submit(store, payload, transport):
    raise NotImplementedError("Persist unknown intent before creating a batch")


def refresh(store, transport):
    raise NotImplementedError("Retrieve only the recorded provider batch")


def collect(store, transport):
    raise NotImplementedError("Validate and cache complete bound results")
