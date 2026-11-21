"""The engine and the two kinds of transaction.

- `read()`: for the application; always rolls back.
- `unit_of_work()`: for the seed job; commits on success, rolls back on error.
"""
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import DisconnectionError, InterfaceError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from ....application.errors import StoreUnavailable
from ..settings import DatabaseCredentials, DatabaseServer

# Connection-level failures only. A `ProgrammingError` (bad SQL, missing column) or an
# `IntegrityError` is a bug in this code and must NOT be reported as a store that is
# temporarily down — it would earn a `503` telling the caller to retry something that
# cannot start working by itself.
_UNREACHABLE = (OperationalError, InterfaceError, DisconnectionError)

_CONNECT_TIMEOUT_SECONDS = 5
_DRIVER = "postgresql+psycopg"


def build_url(server: DatabaseServer, credentials: DatabaseCredentials) -> URL:
    """Builds the connection URL, escaping every component.

    Args:
        server: The database to connect to.
        credentials: The account to connect as.

    Returns:
        The URL.
    """
    return URL.create(
        _DRIVER,
        username=credentials.user,
        password=credentials.password,
        host=server.host,
        port=server.port,
        database=server.name,
    )


class Database:
    """Owns the connection pool of one account.

    Args:
        server: The database to connect to.
        credentials: The account to connect as.
    """

    def __init__(self, server: DatabaseServer, credentials: DatabaseCredentials) -> None:
        self._engine = create_engine(
            build_url(server, credentials),
            pool_pre_ping=True,  # the lab's database is restarted often
            connect_args={
                "connect_timeout": _CONNECT_TIMEOUT_SECONDS,
                "application_name": "promptinj-demo",
            },
        )
        self._sessions = sessionmaker(bind=self._engine, expire_on_commit=False)

    @property
    def engine(self) -> Engine:
        """The engine, for Alembic."""
        return self._engine

    @contextmanager
    def read(self) -> Iterator[Session]:
        """Opens a read-only transaction that is always rolled back.

        Yields:
            The session.

        Raises:
            StoreUnavailable: The database cannot be reached.
        """
        session = self._sessions()
        try:
            yield session
        except _UNREACHABLE as exc:
            raise StoreUnavailable(type(exc).__name__) from exc
        finally:
            session.rollback()
            session.close()

    @contextmanager
    def unit_of_work(self) -> Iterator[Session]:
        """Opens a transaction that commits on success and rolls back on error.

        Yields:
            The session.

        Raises:
            StoreUnavailable: The database cannot be reached.
        """
        session = self._sessions()
        try:
            yield session
            session.commit()
        except _UNREACHABLE as exc:
            session.rollback()
            raise StoreUnavailable(type(exc).__name__) from exc
        except Exception:
            # Rolls back and RE-RAISES UNCHANGED. It translates nothing — a bug inside
            # the transaction keeps its own type and reaches the central handler.
            session.rollback()
            raise
        finally:
            session.close()
