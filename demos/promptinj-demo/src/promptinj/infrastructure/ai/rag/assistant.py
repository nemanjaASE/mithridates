"""Adapts a compiled RAG graph to the `Assistant` port."""
from langgraph.graph.state import CompiledStateGraph

from ....domain.entities import AssistantAnswer, RetrievalFacts
from .spec import RagSpec

BLOCKED_MESSAGE = "[Response blocked by the output check.]"


class RagAssistant:
    """Runs a compiled RAG graph for one question.

    Args:
        spec: The assistant's specification.
        graph: The compiled graph.
    """

    def __init__(self, spec: RagSpec, graph: CompiledStateGraph) -> None:
        self._spec = spec
        self._graph = graph

    def answer(self, question: str, current_user_id: str) -> AssistantAnswer:
        """Answers a question from the retrieved documents.

        Args:
            question: The user's question.
            current_user_id: The user id from the verified token.

        Returns:
            The answer, the prompt and how the context was assembled.
        """
        state = self._graph.invoke(
            {"question": question, "current_user_id": current_user_id}
        )
        raw = state.get("raw_output", "")
        reason = state.get("block_reason")
        chunks = state.get("chunks", [])
        config = self._spec.retrieval
        return AssistantAnswer(
            variant=self._spec.variant,
            answer=BLOCKED_MESSAGE if reason else raw,
            raw_output=raw,
            block_reason=reason,
            prompt=state.get("prompt"),
            retrieval=RetrievalFacts(
                documents=len(chunks),
                scoped_to_owner=config.scope_to_owner,
                safe_fields=config.safe_fields,
                owners=tuple(sorted({c.owner_id for c in chunks})),
            ),
        )
