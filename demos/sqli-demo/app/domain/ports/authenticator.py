from typing import Protocol

from ..models import LoginResult


class Authenticator(Protocol):
    """Checks a username and password against the database."""

    def authenticate(self, username: str, password: str) -> LoginResult:
        """Checks the credentials.

        Args:
            username: The submitted username.
            password: The submitted password.

        Returns:
            The matching users and the executed SQL.

        Raises:
            QueryExecutionError: The database rejected the query.
        """
