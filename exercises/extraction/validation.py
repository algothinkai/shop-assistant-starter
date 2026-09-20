"""Schema plus source-line validation for this deliberately narrow receipt format."""
import re
from datetime import date
from decimal import Decimal
from jsonschema import Draft202012Validator
from .schema import SCHEMA

PATTERNS = {
    "order_id": r"Order:\s*(O-[0-9]{4})",
    "purchase_date": r"Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
    "currency": r"Total:\s*([A-Z]{3})\s+[0-9]+\.[0-9]{2}",
    "total_cents": r"Total:\s*[A-Z]{3}\s+([0-9]+\.[0-9]{2})",
    "customer_name": r"Customer:\s*(.+)",
}


def parsed(field, text):
    match = re.fullmatch(PATTERNS[field], text.strip())
    if not match:
        raise ValueError
    value = match.group(1).strip()
    if field == "total_cents":
        value = int(Decimal(value) * 100)
    elif field == "purchase_date":
        date.fromisoformat(value)
    return value


def validate(source, candidate):
    errors = []
    missing = []
    def error(field, kind, message):
        errors.append({"field": field, "kind": kind, "message": message})
    for issue in Draft202012Validator(SCHEMA).iter_errors(candidate):
        field = str(next(iter(issue.absolute_path), "$"))
        error(field, "schema", "Match the required value/evidence object and its nullable field types; remove extra fields.")
    if errors:
        return {"errors": errors, "missing_fields": missing}
    labels = {"order_id": "Order:", "purchase_date": "Date:", "currency": "Total:", "total_cents": "Total:", "customer_name": "Customer:"}
    complete_lines = {line.strip() for line in source.splitlines()}
    for field, item in candidate.items():
        observed = set()
        unresolved = False
        for line in source.splitlines():
            try:
                observed.add(parsed(field, line))
            except ValueError:
                if line.strip().startswith(labels[field]):
                    unresolved = True
        if unresolved:
            error(field, "source_unresolved", "A labeled source value is present but invalid or unsupported; do not describe it as absent or guess its meaning.")
        if len(observed) > 1:
            error(field, "source_conflict", "The source has conflicting values for this field; preserve the conflict for human review.")
        value, evidence = item["value"], item["evidence"]
        if value is None:
            if evidence is not None:
                error(field, "semantic", "A null value must not carry a claimed supporting excerpt.")
            elif observed:
                error(field, "semantic", "A supported value is present in the provided source; inspect its labeled line rather than leaving it null.")
            elif not unresolved:
                missing.append(field)
            continue
        if not isinstance(evidence, str) or not evidence.strip() or evidence not in source or evidence.strip() not in complete_lines:
            error(field, "semantic", "Provide an exact complete labeled source line, not a truncated substring or external citation.")
            continue
        try:
            expected = parsed(field, evidence)
            if expected != value:
                raise ValueError
        except ValueError:
            error(field, "semantic", "The excerpt must be this field's labeled line and support the normalized value exactly.")
    return {"errors": errors, "missing_fields": missing}
