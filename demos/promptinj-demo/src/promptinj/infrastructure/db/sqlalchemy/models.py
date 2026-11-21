"""ORM models of the tables. Alembic generates the migrations from them."""
from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Index, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Fixed by the embedding model the lab ships with (nomic-embed-text). It is part of the
# schema now that migrations exist: switching to a model with a different width is a
# migration, not a restart. `seeding.py` checks the vectors it is handed against this.
EMBEDDING_DIM = 768


class Base(DeclarativeBase):
    """Declarative base; `Base.metadata` is what Alembic compares against."""


class AccountRow(Base):
    """A row of `accounts`."""

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(Text, nullable=False)
    balance_rsd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Full PAN. Stored in the clear on purpose: the lab needs something real to leak.
    card_number: Mapped[str] = mapped_column(Text, nullable=False)


class CredentialRow(Base):
    """A row of `credentials`, keyed by account id."""

    __tablename__ = "credentials"

    account_id: Mapped[str] = mapped_column(Text, ForeignKey("accounts.id"), primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    # bcrypt hash. The plaintext is never stored.
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)


class DocumentRow(Base):
    """A row of `documents`: the owner, two renderings of the text and the embedding.

    `text` contains every field, including the full card number; `safe_text` only the
    allow-listed fields.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    safe_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)

    __table_args__ = (
        # Approximate nearest-neighbour index. Without it every question would compare
        # the query vector against every row.
        Index(
            "ix_documents_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
