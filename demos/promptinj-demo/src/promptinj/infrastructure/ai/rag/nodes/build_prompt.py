"""Graph node that assembles the prompt from the templates and the retrieved context.

Marking the question as data lowers the chance of an injection but does not prevent it:
the model still receives one text.
"""
from collections.abc import Callable

from .....domain.entities import Prompt
from ...common.prompts import PromptSet, render_context
from ..deps import RagDeps
from ..spec import RagSpec
from ..state import RagState


def make_build_prompt(spec: RagSpec, prompts: PromptSet, _deps: RagDeps) -> Callable[[RagState], dict]:
    """Creates the node that builds the prompt.

    Args:
        spec: The assistant's specification.
        prompts: The assistant's templates.
        _deps: Unused.

    Returns:
        The node function.
    """
    base = spec.render_values()

    def build_prompt(state: RagState) -> dict:
        # The templates are the only format strings; the question and the retrieved text
        # are values. An attacker controls a value, never the template.
        """Renders the system prompt and the user message."""
        values = {
            **base,
            "current_user_id": state["current_user_id"],
            "question": state["question"],
            "context": render_context(state.get("chunks", [])),
        }
        return {
            "prompt": Prompt(
                system=prompts.render("system", **values),
                user=prompts.render("user", **values),
            )
        }

    return build_prompt
