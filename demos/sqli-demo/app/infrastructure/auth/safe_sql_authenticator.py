"""Safe authenticator: the credentials are bound as query parameters.

The password is checked with pgcrypto `crypt()` inside the query, so the stored hash never
leaves the database.
"""
from ...domain.models import LoginResult, QueryTrace, User
from ..persistence.database import PostgresDatabase

_AUTHENTICATE = (
    "SELECT id, username, role FROM users "
    "WHERE username = %s AND password_hash = crypt(%s, password_hash)"
)


class SafeSqlAuthenticator:
    """Authenticates with a parameterized query.

    Args:
        db: Connections for the `lab_app` account.
    """

    def __init__(self, db: PostgresDatabase) -> None:
        self._db = db

    def authenticate(self, username: str, password: str) -> LoginResult:
        """Checks the credentials with a parameterized query.

        Args:
            username: The submitted username.
            password: The submitted password.

        Returns:
            The matching users and the executed SQL.

        Raises:
            QueryExecutionError: The database rejected the query.
        """
        with self._db.connect() as conn:
            row = conn.execute(_AUTHENTICATE, (username, password)).fetchone()
        users = (User(id=str(row[0]), username=row[1], role=row[2]),) if row else ()
        # The password is never echoed back, not even in the (optional) query trace.
        return LoginResult(
            authenticated=row is not None,
            users=users,
            trace=QueryTrace(_AUTHENTICATE, (username, "<password>")),
        )
