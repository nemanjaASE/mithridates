"""Repository for the `documents` table: nearest-neighbour search in SQL.

The vector, the limit and the owner are bound parameters. The column name and the
presence of the owner filter are chosen from literals in this module.
"""
from sqlalchemy import text

from .....domain.entities import RetrievedChunk
from ..session import Database
from ..vector import vector_literal

# Column names are literals here; `safe_fields` selects between them. Nothing a caller
# sends can reach the statement as SQL.
_TEXT_COLUMN = {True: "safe_text", False: "text"}


class PostgresDocumentRepository:
    """Searches the embedded documents.

    Args:
        db: The application's connection pool.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def nearest(
        self, vector: list[float], k: int, owner_id: str | None, *, safe_fields: bool = False
    ) -> list[RetrievedChunk]:
        """Returns the k documents nearest to a vector.

        Args:
            vector: The query vector.
            k: The number of documents to return.
            owner_id: Restricts the search to one owner; None searches every owner.
            safe_fields: Reads `safe_text` instead of `text`.

        Returns:
            The documents, nearest first.
        """
        where = "" if owner_id is None else "WHERE owner_id = :owner"
        column = _TEXT_COLUMN[bool(safe_fields)]
        # `<=>` is cosine DISTANCE (0 = identical), so similarity is 1 - distance and the
        # ORDER BY ascends. Written this way so the HNSW index can serve it.
        # CAST(...) rather than `::vector`: in `text()` a bare `::` collides with the
        # `:param` syntax, and the explicit form says the same thing.
        statement = text(
            f"SELECT owner_id, {column}, 1 - (embedding <=> CAST(:q AS vector)) AS score "
            f"FROM documents {where} "
            "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k"
        )
        params = {"q": vector_literal(vector), "k": k, "owner": owner_id}
        with self._db.read() as session:
            rows = session.execute(statement, params).all()
        # The embeddings themselves are never read back — only the text and the score.
        return [RetrievedChunk(owner_id=r[0], text=r[1], score=float(r[2])) for r in rows]
