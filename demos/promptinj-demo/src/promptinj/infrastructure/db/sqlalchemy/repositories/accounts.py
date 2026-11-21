"""Repository for the `accounts` table. Rows are mapped to domain entities inside the transaction."""
from sqlalchemy.orm import Session

from .....domain.entities import Account
from ..models import AccountRow
from ..session import Database


class PostgresAccountRepository:
    """Reads account records. Makes no access decisions.

    Args:
        db: The application's connection pool.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, account_id: str) -> Account | None:
        """Returns an account by id.

        Args:
            account_id: The account id.

        Returns:
            The account, or None if it does not exist.
        """
        with self._db.read() as session:
            return self._load(session, account_id)

    @staticmethod
    def _load(session: Session, account_id: str) -> Account | None:
        # Primary-key lookup; the id travels as a bound parameter, never as SQL.
        """Reads the account row and maps it to an `Account`."""
        row = session.get(AccountRow, account_id)
        return None if row is None else _to_account(row)


def _to_account(row: AccountRow) -> Account:
    """Maps a row to an `Account`."""
    return Account(
        id=row.id,
        name=row.name,
        email=row.email,
        plan=row.plan,
        balance_rsd=int(row.balance_rsd),
        card_number=row.card_number,
    )
