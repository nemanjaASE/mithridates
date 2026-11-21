"""Retriever that embeds the question and searches the document store."""
from ...application.ports import DocumentSearch, Embedder
from ...domain.entities import RetrievedChunk


class VectorRetriever:
    """Embeds the question and returns the nearest documents.

    Args:
        documents: The document store.
        embedder: The embedding model that also embedded the stored documents.
    """

    def __init__(self, documents: DocumentSearch, embedder: Embedder) -> None:
        self._documents = documents
        self._embedder = embedder

    def retrieve(
        self, query: str, k: int, owner_id: str | None, *, safe_fields: bool = False
    ) -> list[RetrievedChunk]:
        """Returns the k documents most similar to the question.

        Args:
            query: The question.
            k: The number of documents to return.
            owner_id: Restricts the search to one owner; None searches every owner.
            safe_fields: Returns only the allow-listed fields of each document.

        Returns:
            The documents, most similar first.
        """
        vector = self._embedder.embed_query(query)
        return self._documents.nearest(vector, k, owner_id, safe_fields=safe_fields)
