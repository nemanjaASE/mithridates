"""PostgreSQL connections for one database account."""
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

import psycopg
from psycopg.conninfo import make_conninfo

from ..domain.errors import StoreUnavailable

_CONNECT_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class DatabaseServer:
    """Host, port and name of the database."""

    host: str
    port: int
    name: str


@dataclass(frozen=True)
class DatabaseCredentials:
    """User and password of one database account."""

    user: str
    password: str = field(repr=False)


class PostgresDatabase:
    """Opens connections as one database account.

    Args:
        server: The database to connect to.
        credentials: The account to connect as.
    """

    def __init__(self, server: DatabaseServer, credentials: DatabaseCredentials) -> None:
        # make_conninfo escapes every value, so not even the password can add a DSN parameter.
        self._conninfo = make_conninfo(
            host=server.host,
            port=server.port,
            dbname=server.name,
            user=credentials.user,
            password=credentials.password,
            connect_timeout=_CONNECT_TIMEOUT_SECONDS,
            application_name="__NAME__",
        )

    @contextmanager
    def connect(self) -> Iterator[psycopg.Connection]:
        """Opens a connection and closes it on exit.

        Yields:
            The open connection.

        Raises:
            StoreUnavailable: The database cannot be reached.
        """
        try:
            connection = psycopg.connect(self._conninfo, autocommit=True)
        except psycopg.OperationalError as exc:
            raise StoreUnavailable(type(exc).__name__) from exc
        with connection as conn:
            yield conn
