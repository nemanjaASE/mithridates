"""Dependencies of the agent."""
from dataclasses import dataclass
from typing import Protocol

from langchain_core.language_models import BaseChatModel

from ..common.prompts import PromptLoader
from .tools import ToolRegistry


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
class AgentDeps:
    """The model provider, the tools and the prompt loader an agent needs."""

    llm: ChatModelProvider
    prompts: PromptLoader
    # Already bound to their executors, including whatever authorization the application
    # chose for this assistant. The loop never picks a policy.
    tools: ToolRegistry
