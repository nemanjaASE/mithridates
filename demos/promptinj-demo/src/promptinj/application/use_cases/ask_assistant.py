"""Asks a named assistant a question for the authenticated user."""
from ...domain.entities import AssistantAnswer
from ..ports import AssistantRegistry


class AskAssistantUseCase:
    """Runs an assistant for the authenticated user.

    Args:
        registry: Resolves assistants by name.
    """

    def __init__(self, registry: AssistantRegistry) -> None:
        self._registry = registry

    def execute(self, name: str, question: str, current_user_id: str) -> AssistantAnswer:
        """Answers a question with the named assistant.

        Args:
            name: The assistant name.
            question: The user's question.
            current_user_id: The user id from the verified token.

        Returns:
            The answer and its trace.

        Raises:
            UnknownAssistant: No assistant has that name.
        """
        return self._registry.get(name).answer(question, current_user_id)
