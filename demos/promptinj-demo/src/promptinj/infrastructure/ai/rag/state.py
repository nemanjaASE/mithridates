"""State of the RAG graph. Each node writes only its own keys."""
from typing import TypedDict

from ....domain.entities import Prompt, RetrievedChunk


class RagState(TypedDict, total=False):
    """State passed through retrieve, prompt, generate and guard. No node writes `current_user_id`."""

    question: str
    current_user_id: str
    chunks: list[RetrievedChunk]
    prompt: Prompt
    raw_output: str
    block_reason: str | None
