"""What a persistence backend does at startup."""
from typing import Protocol

from .settings import DatabaseCredentials


class Provisioner(Protocol):
    """Migrates the schema, creates the application account and writes the lab data."""

    def migrate(self) -> None:
        """Brings the schema to the latest version."""

    def grant_least_privilege(self, app: DatabaseCredentials) -> None:
        """Creates or updates the application account with read-only access.

        Args:
            app: The application account.
        """

    def write_accounts(self, accounts, password_hashes) -> None:
        """Replaces the accounts and their credentials.

        Args:
            accounts: The accounts.
            password_hashes: The password hash of each account, by id.
        """

    def write_documents(self, embedded_docs) -> None:
        """Replaces the documents.

        Args:
            embedded_docs: Tuples of owner id, text, safe text and embedding.
        """
