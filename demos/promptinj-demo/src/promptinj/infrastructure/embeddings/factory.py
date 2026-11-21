"""Builds the `Embedder` of the configured provider.

Separate from `LLMFactory`: the embedding model belongs to the vector store, so changing
the chat model must not change it.
"""
from collections.abc import Callable

from ...application.errors import ConfigurationError
from ...application.ports import Embedder
from ...config import EmbeddingSpec


def _build_ollama(spec: EmbeddingSpec) -> Embedder:
    """Builds the Ollama embedder."""
    from .ollama import OllamaEmbedder

    return OllamaEmbedder(spec.model, spec.base_url, spec.timeout_seconds)


_PROVIDERS: dict[str, Callable[[EmbeddingSpec], Embedder]] = {
    "ollama": _build_ollama,
}

PROVIDERS: tuple[str, ...] = tuple(sorted(_PROVIDERS))


class EmbedderFactory:
    """Builds the configured embedder once and returns the same instance.

    Args:
        spec: The embedding settings.

    Raises:
        ConfigurationError: The provider is unknown.
    """

    def __init__(self, spec: EmbeddingSpec) -> None:
        if spec.provider not in _PROVIDERS:
            raise ConfigurationError(
                f"Unknown embedding provider {spec.provider!r}. Known: {', '.join(PROVIDERS)}."
            )
        self._spec = spec
        self._embedder: Embedder | None = None

    @property
    def spec(self) -> EmbeddingSpec:
        """The embedding settings."""
        return self._spec

    def build(self) -> Embedder:
        """Returns the embedder, building it on first use.

        Returns:
            The embedder.
        """
        if self._embedder is None:
            self._embedder = _PROVIDERS[self._spec.provider](self._spec)
        return self._embedder

    def describe(self) -> str:
        """Returns the provider and model for `GET /`."""
        return f"{self._spec.provider}:{self._spec.model}"
