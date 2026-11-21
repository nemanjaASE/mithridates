"""Resolves a model role (`strong`, `cheap`) to a chat model.

A new provider is one entry in `_PROVIDERS`. Each model is built on first use and cached
per role.
"""
from collections.abc import Callable, Mapping

from langchain_core.language_models import BaseChatModel

from ...application.errors import ConfigurationError
from ...config import ModelSpec


def _build_ollama(spec: ModelSpec) -> BaseChatModel:
    """Builds the Ollama chat model."""
    from .ollama import build_chat_model

    return build_chat_model(spec)


_PROVIDERS: dict[str, Callable[[ModelSpec], BaseChatModel]] = {
    "ollama": _build_ollama,
}

PROVIDERS: tuple[str, ...] = tuple(sorted(_PROVIDERS))


class LLMFactory:
    """Builds the chat model of each role.

    Args:
        models: The model settings of each role.

    Raises:
        ConfigurationError: A role names an unknown provider.
    """

    def __init__(self, models: Mapping[str, ModelSpec]) -> None:
        for role, spec in models.items():
            if spec.provider not in _PROVIDERS:
                raise ConfigurationError(
                    f"Unknown LLM provider {spec.provider!r} for role {role!r}. "
                    f"Known: {', '.join(PROVIDERS)}."
                )
        self._models = dict(models)
        self._built: dict[str, BaseChatModel] = {}

    @property
    def roles(self) -> tuple[str, ...]:
        """Returns the configured roles."""
        return tuple(sorted(self._models))

    def spec_for(self, role: str) -> ModelSpec:
        """Returns the model settings of a role.

        Args:
            role: The role.

        Returns:
            The model settings.

        Raises:
            ConfigurationError: The role is not configured.
        """
        try:
            return self._models[role]
        except KeyError:
            raise ConfigurationError(
                f"No model configured for role {role!r}. Configured: {', '.join(self.roles)}."
            ) from None

    def for_role(self, role: str) -> BaseChatModel:
        """Returns the chat model of a role, building it on first use.

        Args:
            role: The role.

        Returns:
            The chat model.

        Raises:
            ConfigurationError: The role is not configured.
        """
        spec = self.spec_for(role)
        if role not in self._built:
            self._built[role] = _PROVIDERS[spec.provider](spec)
        return self._built[role]

    def describe(self) -> Mapping[str, str]:
        """Returns a description of each role's model, for `GET /`."""
        return {role: spec.describe() for role, spec in sorted(self._models.items())}
