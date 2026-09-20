"""Implement the two callbacks without changing the registered adapter or checks."""

def callbacks(shop, audit):
    async def before(data, tool_use_id, context):
        raise NotImplementedError("Implement the refund prerequisite hook.")
    async def after(data, tool_use_id, context):
        raise NotImplementedError("Implement the shipping normalization hook.")
    return before, after
