"""Vulnerable authenticator, deliberately: the credentials are formatted into the SQL text.

For the lab only. Example payloads for the username:
    admin'--
    ' OR '1'='1'--
    ' UNION SELECT id, name, value FROM secrets WHERE name = 'flag'--
"""
import psycopg

from ...domain.errors import QueryExecutionError
from ...domain.models import LoginResult, QueryTrace, User
from ..persistence.database import PostgresDatabase


def _run(db: PostgresDatabase, statement: str) -> tuple[User, ...]:
    """Executes a statement and maps the rows to users.

    Args:
        db: The connections to use.
        statement: The complete SQL text.

    Returns:
        The returned users.

    Raises:
        QueryExecutionError: The database rejected the statement.
    """
    with db.connect() as conn:
        try:
            # psycopg type-warns about an f-string query (LiteralString) — intentionally ignored here.
            rows = conn.execute(statement).fetchall()  # type: ignore[arg-type]
        except psycopg.Error as exc:
            raise QueryExecutionError(QueryTrace(statement)) from exc
    # After a UNION attack the "user" may be any row from the database.
    # str(r[0]): psycopg returns a uuid column as uuid.UUID, the domain keeps id as text.
    return tuple(User(id=str(r[0]), username=r[1], role=r[2]) for r in rows)


class VulnerableSqlAuthenticator:
    """Authenticates with a query built by string formatting.

    Args:
        db: Connections for the `lab_legacy` account.
    """

    def __init__(self, db: PostgresDatabase) -> None:
        self._db = db

    def authenticate(self, username: str, password: str) -> LoginResult:
        """Checks the credentials with a query that contains them as text.

        Args:
            username: The submitted username, inserted into the SQL unescaped.
            password: The submitted password, inserted into the SQL unescaped.

        Returns:
            The users the query returned and the executed SQL.

        Raises:
            QueryExecutionError: The database rejected the query.
        """
        statement = (
            "SELECT id, username, role FROM users "
            f"WHERE username = '{username}' AND password_hash = crypt('{password}', password_hash)"
        )
        users = _run(self._db, statement)
        return LoginResult(authenticated=bool(users), users=users, trace=QueryTrace(statement))
