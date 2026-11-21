"""Helpers for calling a chat model."""
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from ....application.errors import LanguageModelUnavailable
from ...llm.transport import TRANSPORT_FAILURES

_logger = logging.getLogger("promptinj.ai")


def text_of(content: str | list) -> str:
    """Flattens a message's content to plain text.

    Args:
        content: A string or a list of content blocks.

    Returns:
        The text.
    """
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) else str(block) for block in content
    )


def call_chat_model(model: BaseChatModel, messages: list[BaseMessage]) -> BaseMessage:
    """Calls the chat model.

    Args:
        model: The chat model.
        messages: The messages to send.

    Returns:
        The model's reply.

    Raises:
        LanguageModelUnavailable: The model cannot be reached or timed out.
    """
    try:
        return model.invoke(messages)
    except TRANSPORT_FAILURES as exc:
        _logger.warning("llm_unavailable type=%s", type(exc).__name__)
        raise LanguageModelUnavailable(str(exc)) from exc
