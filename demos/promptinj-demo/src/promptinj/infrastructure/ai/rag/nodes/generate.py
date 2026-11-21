"""Graph node that calls the chat model."""
from collections.abc import Callable

from langchain_core.messages import HumanMessage, SystemMessage

from ...common.messages import call_chat_model, text_of
from ..deps import RagDeps
from ..spec import RagSpec
from ..state import RagState


def make_generate(spec: RagSpec, deps: RagDeps) -> Callable[[RagState], dict]:
    """Creates the node that calls the model of the spec's role.

    Args:
        spec: The assistant's specification.
        deps: The assistant's dependencies.

    Returns:
        The node function.
    """
    model = deps.llm.for_role(spec.model_role)

    def generate(state: RagState) -> dict:
        """Sends the prompt to the model and stores its output."""
        prompt = state["prompt"]
        response = call_chat_model(
            model, [SystemMessage(content=prompt.system), HumanMessage(content=prompt.user)]
        )
        return {"raw_output": text_of(response.content)}

    return generate
