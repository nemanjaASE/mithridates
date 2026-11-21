"""Reads the environment into settings. The only module that reads `os.environ`.

Passwords and the signing key have no default value; a missing one raises
`ConfigurationError` at startup.
"""
import os
from dataclasses import dataclass

from .domain.errors import ConfigurationError
from .infrastructure.persistence import DatabaseCredentials, DatabaseServer
from .infrastructure.tokens import JwtSettings


def _env_bool(name: str, default: bool) -> bool:
    """Reads a boolean variable, or returns `default` when it is not set."""
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes"}


def _require(name: str) -> str:
    """Reads a required variable, or raises `ConfigurationError`."""
    value = os.environ.get(name)
    if not value:
        raise ConfigurationError(f"Missing required env variable {name}.")
    return value


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


@dataclass(frozen=True)
class Settings:
    """Settings of the application process."""

    server: DatabaseServer
    # The vulnerable adapters use the "legacy" account, the safe one a least-privilege account.
    legacy_db: DatabaseCredentials
    app_db: DatabaseCredentials
    jwt: JwtSettings
    # Returns the executed SQL in the response. Off by default: it discloses the query.
    expose_query_trace: bool = False
    enable_debug_endpoints: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """Reads the settings from the environment.

        Returns:
            The settings.

        Raises:
            ConfigurationError: A required variable is missing or invalid.
        """
        return cls(
            server=_server_from_env(),
            legacy_db=_credentials_from_env("DB_LEGACY"),
            app_db=_credentials_from_env("DB_APP"),
            jwt=JwtSettings(
                secret=_require("JWT_SECRET"),
                ttl_seconds=int(os.environ.get("JWT_TTL_SECONDS", "900")),
            ),
            expose_query_trace=_env_bool("EXPOSE_QUERY_TRACE", False),
            enable_debug_endpoints=_env_bool("ENABLE_DEBUG_ENDPOINTS", True),
        )


@dataclass(frozen=True)
class SeedSettings:
    """Settings of the seed job, the only process that uses the admin account."""

    server: DatabaseServer
    admin: DatabaseCredentials
    legacy_db: DatabaseCredentials
    app_db: DatabaseCredentials

    @classmethod
    def from_env(cls) -> "SeedSettings":
        """Reads the seed settings from the environment.

        Returns:
            The settings.

        Raises:
            ConfigurationError: A required variable is missing.
        """
        return cls(
            server=_server_from_env(),
            admin=_credentials_from_env("DB_ADMIN"),
            legacy_db=_credentials_from_env("DB_LEGACY"),
            app_db=_credentials_from_env("DB_APP"),
        )
