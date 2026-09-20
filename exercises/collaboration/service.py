"""Thin adapter: reuse the shop's actual event log, never synthesize success."""

from .report import summarize_run


def case_report(shop, run_id):
    return summarize_run(shop.events(), run_id)
