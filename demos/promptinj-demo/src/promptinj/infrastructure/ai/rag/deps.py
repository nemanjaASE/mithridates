"""Dependencies of the RAG graph."""
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from langchain_core.language_models import BaseChatModel

from ....application.ports import DocumentRetriever, OutputFilter
from ..common.prompts import PromptLoader


class ChatModelProvider(Protocol):
    """Resolves a model role to a chat model."""

    def for_role(self, role: str) -> BaseChatModel:
        """Returns the chat model of a role.

        Args:
            role: `"strong"` or `"cheap"`.

        Returns:
            The chat model.
        """


@dataclass(frozen=True)
class RagDeps:
    """The retriever, model provider, prompt loader and output filters a RAG graph needs."""

    llm: ChatModelProvider
    prompts: PromptLoader
    retriever: DocumentRetriever
    # Resolved by the name a spec lists in `output_filters`.
    output_filters: Mapping[str, OutputFilter]
