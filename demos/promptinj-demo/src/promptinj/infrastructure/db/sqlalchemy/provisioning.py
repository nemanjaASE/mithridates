"""SQLAlchemy implementation of `Provisioner`."""
from ..settings import DatabaseCredentials, DatabaseServer
from . import seeding
from .migrate import upgrade_to_head
from .privileges import grant_least_privilege
from .session import Database


class SqlAlchemyProvisioner:
    """Provisions the database as the admin account.

    Args:
        server: The database to connect to.
        admin: The admin account.
    """

    def __init__(self, server: DatabaseServer, admin: DatabaseCredentials) -> None:
        self._db = Database(server, admin)

    def migrate(self) -> None:
        """Brings the schema to the latest version."""
        upgrade_to_head(self._db)

    def grant_least_privilege(self, app: DatabaseCredentials) -> None:
        # After `migrate`, because SELECT can only be granted on tables that exist.
        """Creates or updates the application account.

        Args:
            app: The application account.
        """
        grant_least_privilege(self._db, app)

    def write_accounts(self, accounts, password_hashes) -> None:
        """Replaces the accounts and their credentials.

        Args:
            accounts: The accounts.
            password_hashes: The password hash of each account, by id.
        """
        seeding.reset_accounts(self._db, accounts, password_hashes)

    def write_documents(self, embedded_docs) -> None:
        """Replaces the documents.

        Args:
            embedded_docs: Tuples of owner id, text, safe text and embedding.
        """
        seeding.reset_documents(self._db, embedded_docs)
