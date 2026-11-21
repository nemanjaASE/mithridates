"""Embedding model served by Ollama.

The same model embeds the stored documents and the query. Each call has an explicit HTTP
timeout, since the Ollama client waits indefinitely by default.
"""
import logging

from langchain_ollama import OllamaEmbeddings

from ...application.errors import LanguageModelUnavailable
from ..llm.transport import TRANSPORT_FAILURES

_logger = logging.getLogger("promptinj.embeddings")


class OllamaEmbedder:
    """Embeds text with an Ollama model.

    Args:
        model: The model name.
        base_url: The Ollama server URL.
        timeout_seconds: The timeout of each HTTP call.
    """

    def __init__(self, model: str, base_url: str, timeout_seconds: float) -> None:
        self._model = model
        self._embeddings = OllamaEmbeddings(
            model=model, base_url=base_url, client_kwargs={"timeout": timeout_seconds}
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embeds several texts.

        Args:
            texts: The texts to embed.

        Returns:
            One vector per text.

        Raises:
            LanguageModelUnavailable: The model cannot be reached.
        """
        return self._call(lambda: self._embeddings.embed_documents(list(texts)))

    def embed_query(self, text: str) -> list[float]:
        """Embeds one query.

        Args:
            text: The query.

        Returns:
            The vector.

        Raises:
            LanguageModelUnavailable: The model cannot be reached.
        """
        return self._call(lambda: self._embeddings.embed_query(text))

    def _call(self, run):
        """Runs a client call; translates only transport failures to `LanguageModelUnavailable`."""
        try:
            return run()
        except TRANSPORT_FAILURES as exc:
            _logger.warning(
                "Embedding model unavailable (model=%s): %s", self._model, type(exc).__name__
            )
            raise LanguageModelUnavailable("embedding model unavailable") from exc
