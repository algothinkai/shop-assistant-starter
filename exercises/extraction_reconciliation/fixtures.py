SOURCE = """Receipt: R-4001
Item: paper filter x2 @ USD 19.75
Item: cleaning brush x1 @ USD 8.00
Subtotal: USD 47.50
Tax: USD 3.80
Shipping: USD 5.00
Discount: USD 2.00
Total: USD 54.30
Category: filter
"""

SCENARIOS = {
    "consistent": SOURCE,
    "mismatch": SOURCE.replace("Total: USD 54.30", "Total: USD 55.30"),
    "missing-charge": SOURCE.replace("Shipping: USD 5.00\n", ""),
    "mixed-currency": SOURCE.replace("Tax: USD", "Tax: EUR"),
    "other": SOURCE.replace("Category: filter", "Category: repair kit"),
    "unclear": SOURCE.replace("Category: filter", "Category: ?"),
}
