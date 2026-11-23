"""Reads the environment into settings. The only module that reads `os.environ`.

The signing key and the passwords have no default value; a missing setting raises
`ConfigurationError` at startup.
"""
import os
from dataclasses import dataclass

from .domain.errors import ConfigurationError
# [postgres]
from .infrastructure.database import DatabaseCredentials, DatabaseServer
# [/postgres]
from .infrastructure.tokens import JwtSettings

# Where the host reaches the service when nothing else is set.
LOCAL_URL = "http://127.0.0.1:8000"


def _require(name: str) -> str:
    """Reads a required variable, or raises `ConfigurationError`."""
    value = os.environ.get(name)
    if not value:
        raise ConfigurationError(f"Missing required env variable {name}.")
    return value
# [postgres]


def _server_from_env() -> DatabaseServer:
    """Reads the database host, port and name."""
    return DatabaseServer(
        host=_require("DB_HOST"),
        port=int(os.environ.get("DB_PORT", "5432")),
        name=_require("DB_NAME"),
    )


def _credentials_from_env(prefix: str) -> DatabaseCredentials:
    """Reads the user and password of one database account."""
    return DatabaseCredentials(user=_require(f"{prefix}_USER"), password=_require(f"{prefix}_PASSWORD"))
# [/postgres]


@dataclass(frozen=True)
class Settings:
    """Settings of the application process."""

    jwt: JwtSettings
    # [postgres]
    server: DatabaseServer
    app_db: DatabaseCredentials
    # [/postgres]
    # The address printed when the service is ready; compose sets the published port.
    public_url: str = LOCAL_URL

    @classmethod
    def from_env(cls) -> Settings:
        """Reads the settings from the environment.

        Returns:
            The settings.

        Raises:
            ConfigurationError: A required variable is missing or invalid.
        """
        return cls(
            jwt=JwtSettings(
                secret=_require("JWT_SECRET"),
                ttl_seconds=int(os.environ.get("JWT_TTL_SECONDS", "900")),
            ),
            # [postgres]
            server=_server_from_env(),
            app_db=_credentials_from_env("DB_APP"),
            # [/postgres]
            public_url=os.environ.get("PUBLIC_URL", LOCAL_URL),
        )
# [postgres]


@dataclass(frozen=True)
class SeedSettings:
    """Settings of the seed job, the only process that uses the admin account."""

    server: DatabaseServer
    admin: DatabaseCredentials
    app_db: DatabaseCredentials

    @classmethod
    def from_env(cls) -> SeedSettings:
        """Reads the seed settings from the environment.

        Returns:
            The settings.

        Raises:
            ConfigurationError: A required variable is missing.
        """
        return cls(
            server=_server_from_env(),
            admin=_credentials_from_env("DB_ADMIN"),
            app_db=_credentials_from_env("DB_APP"),
        )
# [/postgres]
