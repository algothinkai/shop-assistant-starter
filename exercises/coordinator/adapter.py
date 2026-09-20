"""Learner scope: SDK configuration and observed workflow evidence."""


def build_options(runtime, cwd, model):
    raise NotImplementedError("Configure the coordinator and scoped subagents")


async def consume(messages, runtime):
    raise NotImplementedError("Require actual delegation/tool/terminal evidence")
