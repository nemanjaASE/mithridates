"""Writes the lab data, each step in one transaction. Runs as admin."""
import logging

from sqlalchemy import delete

from ....application.errors import ConfigurationError
from .models import EMBEDDING_DIM, AccountRow, CredentialRow, DocumentRow
from .session import Database

_logger = logging.getLogger("promptinj.db")


def reset_accounts(db: Database, accounts, password_hashes) -> None:
    """Replaces the accounts and their credentials in one transaction.

    Args:
        db: The admin connection pool.
        accounts: The accounts.
        password_hashes: The password hash of each account, by id.
    """
    with db.unit_of_work() as session:
        # Documents reference an owner by convention, credentials by foreign key, so the
        # deletes go child-first.
        session.execute(delete(CredentialRow))
        session.execute(delete(AccountRow))
        session.flush()
        session.add_all(
            AccountRow(
                id=a.id,
                name=a.name,
                email=a.email,
                plan=a.plan,
                balance_rsd=a.balance_rsd,
                card_number=a.card_number,
            )
            for a in accounts
        )
        session.flush()  # accounts must exist before credentials can reference them
        session.add_all(
            CredentialRow(account_id=a.id, email=a.email, password_hash=password_hashes[a.email])
            for a in accounts
            if a.email in password_hashes
        )
    _logger.info("Seeded %d accounts.", len(accounts))


def reset_documents(db: Database, embedded_docs) -> None:
    """Replaces the documents in one transaction.

    Args:
        db: The admin connection pool.
        embedded_docs: Tuples of owner id, text, safe text and embedding.
    """
    _check_dimensions(embedded_docs)
    with db.unit_of_work() as session:
        session.execute(delete(DocumentRow))
        session.flush()
        session.add_all(
            DocumentRow(owner_id=owner, text=text, safe_text=safe, embedding=vector)
            for owner, text, safe, vector in embedded_docs
        )
    _logger.info("Seeded %d documents.", len(embedded_docs))


def _check_dimensions(embedded_docs) -> None:
    """Checks that every embedding has the width the schema expects.

    Raises:
        ConfigurationError: An embedding has a different width.
    """
    widths = {len(vector) for *_, vector in embedded_docs}
    if widths and widths != {EMBEDDING_DIM}:
        raise ConfigurationError(
            f"The embedding model produced vectors of width {sorted(widths)}, but the "
            f"`documents.embedding` column is vector({EMBEDDING_DIM}). Changing EMBED_MODEL "
            "to one with a different width needs a migration, not just a re-seed."
        )
