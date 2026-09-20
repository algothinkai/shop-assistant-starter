"""Implement source-bound review planning and aggregation for this checkpoint."""


class ReviewFailure(ValueError):
    pass


def plan(files):
    raise NotImplementedError("Plan local passes and cross-file integration")


def aggregate(files, reports, prior=None):
    raise NotImplementedError("Validate findings and preserve incomplete review work")
