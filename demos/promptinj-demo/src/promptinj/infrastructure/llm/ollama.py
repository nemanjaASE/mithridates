"""Chat model served by Ollama. All settings come from the `ModelSpec`."""
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from ...config import ModelSpec


def build_chat_model(spec: ModelSpec) -> BaseChatModel:
    """Builds an Ollama chat model.

    Args:
        spec: The model settings.

    Returns:
        The chat model.
    """
    return ChatOllama(
        model=spec.model,
        base_url=spec.base_url,
        temperature=spec.temperature,
        num_predict=spec.max_tokens,
        client_kwargs={"timeout": spec.timeout_seconds},
    )
