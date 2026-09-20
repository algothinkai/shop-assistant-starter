"""Implement the current checkpoint only; see stages/05-evaluation.md."""
FIELDS = ("order_id", "purchase_date", "currency", "total_cents", "customer_name")


def evaluate(calibration, evaluation, *, target_accuracy=0.9, min_support=2,
             sample_per_stratum=1, seed=7):
    """Return segment metrics, calibration thresholds, review routing and samples."""
    raise NotImplementedError("Stage 5 evaluation: implement labeled evaluation")
