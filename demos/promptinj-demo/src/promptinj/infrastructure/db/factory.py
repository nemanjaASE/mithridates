"""Selects the persistence backend. A new backend is a folder here and one line in `_BACKENDS`."""
from collections.abc import Callable
from dataclasses import dataclass

from ...application.errors import ConfigurationError
from ...application.ports import AccountRepository, CredentialStore, DocumentSearch
from ...config import PersistenceSpec
from .provisioning import Provisioner
from .settings import DatabaseCredentials, DatabaseServer


@dataclass(frozen=True)
class Stores:
    """The account, credential and document stores of one backend."""

    accounts: AccountRepository
    credentials: CredentialStore
    documents: DocumentSearch


def _sqlalchemy_stores(server: DatabaseServer, credentials: DatabaseCredentials) -> Stores:
    """Builds the SQLAlchemy stores."""
    from .sqlalchemy.repositories.accounts import PostgresAccountRepository
    from .sqlalchemy.repositories.credentials import PostgresCredentialStore
    from .sqlalchemy.repositories.documents import PostgresDocumentRepository
    from .sqlalchemy.session import Database

    db = Database(server, credentials)  # one engine, one pool, three readers
    return Stores(
        accounts=PostgresAccountRepository(db),
        credentials=PostgresCredentialStore(db),
        documents=PostgresDocumentRepository(db),
    )


def _sqlalchemy_provisioner(server: DatabaseServer, admin: DatabaseCredentials) -> Provisioner:
    """Builds the SQLAlchemy provisioner."""
    from .sqlalchemy.provisioning import SqlAlchemyProvisioner

    return SqlAlchemyProvisioner(server, admin)


_BACKENDS: dict[str, tuple[Callable[..., Stores], Callable[..., Provisioner]]] = {
    "sqlalchemy": (_sqlalchemy_stores, _sqlalchemy_provisioner),
}

BACKENDS: tuple[str, ...] = tuple(sorted(_BACKENDS))


class PersistenceFactory:
    """Builds the stores and the provisioner of the configured backend.

    Args:
        spec: The configured backend.

    Raises:
        ConfigurationError: The backend is unknown.
    """

    def __init__(self, spec: PersistenceSpec) -> None:
        if spec.backend not in _BACKENDS:
            raise ConfigurationError(
                f"Unknown persistence backend {spec.backend!r}. Known: {', '.join(BACKENDS)}."
            )
        self._spec = spec
        self._stores, self._provisioner = _BACKENDS[spec.backend]

    def stores(self, server: DatabaseServer, credentials: DatabaseCredentials) -> Stores:
        """Builds the stores for the application account.

        Args:
            server: The database to connect to.
            credentials: The read-only application account.

        Returns:
            The stores.
        """
        return self._stores(server, credentials)

    def provisioner(self, server: DatabaseServer, admin: DatabaseCredentials) -> Provisioner:
        """Builds the provisioner for the admin account. Used only by the seed job.

        Args:
            server: The database to connect to.
            admin: The admin account.

        Returns:
            The provisioner.
        """
        return self._provisioner(server, admin)

    def describe(self) -> str:
        """Returns the backend name for `GET /`."""
        return self._spec.backend
