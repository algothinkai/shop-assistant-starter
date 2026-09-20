"""Stage 2 learner start: implement the explicit Messages API loop here."""


def run_loop(send, shop, prompt, *, max_turns=6):
    """Return status, stop_reason, text, tool_errors, history and trace.

    Only end_turn means ended (not a resolved support case). Safety exhaustion
    means interrupted. See the authored checkpoint before reading the reference.
    """
    raise NotImplementedError("Stage 2 loop is the exercise; follow stages/02-tool-loop.md.")
