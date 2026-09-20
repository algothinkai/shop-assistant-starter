"""Implement stated/calculated separation and honest category handling."""
from jsonschema import Draft202012Validator
from .schema import SCHEMA


def reconcile(source):
    import re
    if not isinstance(source, str) or not source.strip() or len(source) > 20000:
        raise ValueError("Use a nonempty receipt of at most 20000 characters")
    fields = {k: [] for k in ("Subtotal", "Tax", "Shipping", "Discount", "Total")}
    items, categories, receipts, observations, issues = [], [], [], [], []
    malformed = False
    money = r"([A-Z]{3}) ([0-9]{1,12})\.([0-9]{2})"
    def cents(whole, fraction):
        return int(whole) * 100 + int(fraction)
    for raw in source.splitlines():
        line = raw.strip()
        if not line:
            continue
        item = re.fullmatch(r"Item: (.+) x([1-9][0-9]{0,5}) @ " + money, line)
        amount = re.fullmatch(r"(Subtotal|Tax|Shipping|Discount|Total): " + money, line)
        category = re.fullmatch(r"Category: (\S(?:.*\S)?)", line)
        receipt = re.fullmatch(r"Receipt: (R-[0-9]{4})", line)
        if item:
            name, quantity, currency, whole, fraction = item.groups()
            value = cents(whole, fraction)
            items.append((int(quantity), currency, value))
            observations.append({"field": "Item", "source": raw, "quantity": int(quantity), "currency": currency, "unit_cents": value})
        elif amount:
            field, currency, whole, fraction = amount.groups()
            value = cents(whole, fraction)
            fields[field].append((currency, value))
            observations.append({"field": field, "source": raw, "currency": currency, "cents": value})
        elif category:
            categories.append(category.group(1))
            observations.append({"field": "Category", "source": raw, "value": category.group(1)})
        elif receipt:
            receipts.append(receipt.group(1))
            observations.append({"field": "Receipt", "source": raw, "value": receipt.group(1)})
        else:
            malformed = True
            issues.append("unresolved_line")
            observations.append({"field": "unresolved", "source": raw})
    conflict = False
    if len(receipts) != 1:
        issues.append("receipt_identity_required")
        malformed = True
    if not items:
        issues.append("items_required")
    for field, values in fields.items():
        if len(values) != 1:
            issues.append("missing_or_repeated_" + field.lower())
        if len(set(values)) > 1:
            conflict = True
            issues.append("conflicting_" + field.lower())
    currencies = {currency for _, currency, _ in items}
    currencies.update(currency for values in fields.values() for currency, _ in values)
    if len(currencies) != 1:
        issues.append("currency_unresolved")
    stated = fields["Total"][0][1] if len(fields["Total"]) == 1 else None
    item_sum = sum(quantity * value for quantity, _, value in items) if items and len(currencies) == 1 and not malformed else None
    if item_sum is not None and len(fields["Subtotal"]) == 1 and fields["Subtotal"][0][1] != item_sum:
        issues.append("subtotal_mismatch")
        conflict = True
    calculated = None
    if item_sum is not None and all(len(fields[k]) == 1 for k in ("Subtotal", "Tax", "Shipping", "Discount")):
        calculated = item_sum + fields["Tax"][0][1] + fields["Shipping"][0][1] - fields["Discount"][0][1]
        if stated is not None and calculated != stated:
            issues.append("total_mismatch")
            conflict = True
        if calculated < 0:
            issues.append("negative_calculated_total")
    category_value, detail = "unclear", None
    if len(categories) != 1:
        issues.append("missing_or_repeated_category")
        if len({v.casefold() for v in categories}) > 1:
            conflict = True
    else:
        normalized = categories[0].casefold()
        if normalized in ("?", "unclear", "other"):
            issues.append("category_unresolved")
        elif normalized in ("kettle", "grinder", "filter"):
            category_value = normalized
        else:
            category_value, detail = "other", categories[0]
    return {"status": "needs_human_review" if issues else "reconciled",
            "record": {"stated_total_cents": stated, "calculated_total_cents": calculated,
                       "difference_cents": calculated - stated if calculated is not None and stated is not None else None,
                       "conflict_detected": conflict, "category": category_value, "category_detail": detail},
            "item_subtotal_cents": item_sum, "observations": observations,
            "issues": list(dict.fromkeys(issues))}


def validate_candidate(source, candidate):
    """A proposed structured record must match source-derived facts, not just types."""
    report = reconcile(source)
    errors = []
    if list(Draft202012Validator(SCHEMA).iter_errors(candidate)):
        errors.append("schema")
    else:
        errors.extend(field for field, expected in report["record"].items() if candidate[field] != expected)
    return {"status": "needs_human_review" if report["issues"] else "candidate_errors" if errors else "validated_candidate",
            "candidate_errors": errors, "source_report": report}
