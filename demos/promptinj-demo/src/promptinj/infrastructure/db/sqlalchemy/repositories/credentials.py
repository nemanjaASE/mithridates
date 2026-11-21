"""Repository for the `credentials` table. Reads only password hashes."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .....domain.entities import Credential
from ..models import CredentialRow
from ..session import Database


class PostgresCredentialStore:
    """Looks up login credentials by email.

    Args:
        db: The application's connection pool.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def find_credential(self, email: str) -> Credential | None:
        """Returns the credential for an email address.

        Args:
            email: The login email.

        Returns:
            The credential, or None if the email is unknown.
        """
        with self._db.read() as session:
            return self._load(session, email)

    @staticmethod
    def _load(session: Session, email: str) -> Credential | None:
        """Reads the credential row and maps it to a `Credential`."""
        statement = select(CredentialRow).where(CredentialRow.email == email)
        row = session.scalars(statement).one_or_none()
        # Mapped here, inside the transaction: the ORM row does not leave this method.
        return (
            None
            if row is None
            else Credential(
                user_id=row.account_id, email=row.email, password_hash=row.password_hash
            )
        )
