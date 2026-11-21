"""Graph node that retrieves the documents for the model's context.

`scope_to_owner` restricts the search to the token's user; `safe_fields` selects the
allow-listed projection. Everything after this node is the same for both variants.
"""
from collections.abc import Callable

from ..deps import RagDeps
from ..spec import RagSpec
from ..state import RagState


def make_retrieve(spec: RagSpec, deps: RagDeps) -> Callable[[RagState], dict]:
    """Creates the node that retrieves the documents.

    Args:
        spec: The assistant's specification.
        deps: The assistant's dependencies.

    Returns:
        The node function.
    """
    config = spec.retrieval

    def retrieve(state: RagState) -> dict:
        """Retrieves the documents for the question and records how."""
        owner_id = state["current_user_id"] if config.scope_to_owner else None
        chunks = deps.retriever.retrieve(
            state["question"], config.top_k, owner_id, safe_fields=config.safe_fields
        )
        return {"chunks": chunks}

    return retrieve
