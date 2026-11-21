"""PostgreSQL connections for one database account."""
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.conninfo import make_conninfo

from ...domain.errors import StoreUnavailable
from .connection_settings import DatabaseCredentials, DatabaseServer

_CONNECT_TIMEOUT_SECONDS = 5


class PostgresDatabase:
    """Opens connections as one database account.

    Args:
        server: The database to connect to.
        credentials: The account to connect as.
    """

    def __init__(self, server: DatabaseServer, credentials: DatabaseCredentials) -> None:
        # make_conninfo escapes the values, so even the password cannot "inject" a DSN parameter.
        self._conninfo = make_conninfo(
            host=server.host,
            port=server.port,
            dbname=server.name,
            user=credentials.user,
            password=credentials.password,
            connect_timeout=_CONNECT_TIMEOUT_SECONDS,
            application_name="sqli-demo",
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
            raise StoreUnavailable(str(type(exc).__name__)) from exc
        with connection as conn:
            yield conn
