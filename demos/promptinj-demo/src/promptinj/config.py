"""Reads the environment into settings. The only module that reads `os.environ`.

Chat models are configured by role (`strong`, `cheap`); the embedding model separately.
`JWT_SECRET` has no default; a missing setting raises `ConfigurationError` at startup.
"""
import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from .application.errors import ConfigurationError

# Imported directly rather than through the package, so merely loading config does not
# pull in psycopg or PyJWT; those are imported only when a connection is opened or a
# token is signed.
from .infrastructure.db.settings import DatabaseCredentials, DatabaseServer
from .infrastructure.security.authentication.jwt_settings import JwtSettings

DEFAULT_DB_BACKEND = "sqlalchemy"
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

STRONG = "strong"  # tool calling: the agent loop
CHEAP = "cheap"  # a single completion: the RAG assistant
ROLES = (STRONG, CHEAP)


@dataclass(frozen=True)
class ModelSpec:
    """Provider, model and limits of one chat model."""

    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_OLLAMA_URL
    # 0.0 by default because a demonstration has to repeat: the same payload should give
    # the same answer twice in a row. Raising it is a legitimate thing to do in the lab —
    # it shows that a successful injection is a probability, not a certainty — so it is a
    # setting rather than a constant. `GET /` reports any non-zero value, because at that
    # point two runs are no longer comparable.
    temperature: float = 0.0
    max_tokens: int = 512  # upper bound on the tokens of one response
    timeout_seconds: float = 120.0  # a small local model on CPU is slow

    def __post_init__(self) -> None:
        """Rejects invalid limits."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ConfigurationError(
                f"temperature must be between 0.0 and 2.0, got {self.temperature}."
            )

    def describe(self) -> str:
        """Describes the model for `GET /`.

        Returns:
            The description.
        """
        base = f"{self.provider}:{self.model}"
        return base if self.temperature == 0.0 else f"{base}@t={self.temperature:g}"


@dataclass(frozen=True)
class PersistenceSpec:
    """The database backend that implements the stores."""

    backend: str = DEFAULT_DB_BACKEND


@dataclass(frozen=True)
class EmbeddingSpec:
    """Provider and model of the embeddings."""

    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_EMBED_MODEL
    base_url: str = DEFAULT_OLLAMA_URL
    # A separate, much smaller budget: one embedding call should fail long before a
    # generation would. This bounds a single HTTP call, not the whole request.
    timeout_seconds: float = 30.0


def _default_models() -> dict[str, ModelSpec]:
    """Returns the default model for each role."""
    return {role: ModelSpec() for role in ROLES}


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


def _per_role(name: str, role: str) -> str | None:
    """Returns `<NAME>_<ROLE>`, else `<NAME>`, else None. Empty counts as unset."""
    return os.environ.get(f"{name}_{role.upper()}") or os.environ.get(name) or None


def _models_from_env() -> dict[str, ModelSpec]:
    """Reads the chat model of each role."""
    provider = os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER
    base_url = os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_URL
    defaults = ModelSpec()
    return {
        role: ModelSpec(
            provider=provider,
            model=_per_role("MODEL", role) or defaults.model,
            base_url=base_url,
            temperature=float(_per_role("TEMPERATURE", role) or defaults.temperature),
            max_tokens=int(_per_role("MAX_TOKENS", role) or defaults.max_tokens),
            timeout_seconds=float(
                _per_role("TIMEOUT_SECONDS", role) or defaults.timeout_seconds
            ),
        )
        for role in ROLES
    }


def _embeddings_from_env() -> EmbeddingSpec:
    """Reads the embedding model."""
    defaults = EmbeddingSpec()
    return EmbeddingSpec(
        provider=os.environ.get("EMBED_PROVIDER") or DEFAULT_PROVIDER,
        model=os.environ.get("EMBED_MODEL") or defaults.model,
        base_url=os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_URL,
        timeout_seconds=float(os.environ.get("EMBED_TIMEOUT_SECONDS", defaults.timeout_seconds)),
    )


@dataclass(frozen=True)
class Settings:
    # PostgreSQL + pgvector is the only store, and it is required. These dataclasses are
    # plain values, so constructing Settings opens no connection.
    """Settings of the application process."""

    database: DatabaseServer
    app_db: DatabaseCredentials
    # No default: a signing key is a secret, and a secret that has a value in source is
    # a secret everybody who cloned the repository already knows.
    jwt: JwtSettings
    persistence: PersistenceSpec = field(default_factory=PersistenceSpec)
    models: Mapping[str, ModelSpec] = field(default_factory=_default_models)
    embeddings: EmbeddingSpec = field(default_factory=EmbeddingSpec)
    rag_top_k: int = 4  # how many documents the retriever returns
    # Educational lab features; in a real app both would be turned off.
    expose_prompt_trace: bool = True
    # The raw output bypasses the output check, so it is off by default.
    expose_raw_output: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        """Reads the settings from the environment.

        Returns:
            The settings.

        Raises:
            ConfigurationError: A required variable is missing or invalid.
        """
        if not os.environ.get("DB_HOST"):
            raise ConfigurationError(
                "DB_HOST is not set. This service reads accounts and documents from "
                "PostgreSQL/pgvector and has no in-memory fallback; start it with "
                "`docker compose up`."
            )
        jwt = JwtSettings(
            secret=_require("JWT_SECRET"),
            ttl_seconds=int(os.environ.get("JWT_TTL_SECONDS", "900")),
        )
        defaults = cls(
            database=_server_from_env(), app_db=_credentials_from_env("DB_APP"), jwt=jwt
        )
        return cls(
            database=defaults.database,
            app_db=defaults.app_db,
            jwt=jwt,
            persistence=PersistenceSpec(
                backend=os.environ.get("DB_BACKEND") or DEFAULT_DB_BACKEND
            ),
            models=_models_from_env(),
            embeddings=_embeddings_from_env(),
            rag_top_k=int(os.environ.get("RAG_TOP_K", defaults.rag_top_k)),
            expose_prompt_trace=_env_bool("EXPOSE_PROMPT_TRACE", defaults.expose_prompt_trace),
            expose_raw_output=_env_bool("EXPOSE_RAW_OUTPUT", defaults.expose_raw_output),
        )


@dataclass(frozen=True)
class SeedSettings:
    """Settings of the seed job, the only process that uses the admin account."""

    server: DatabaseServer
    admin: DatabaseCredentials
    app_db: DatabaseCredentials
    persistence: PersistenceSpec = field(default_factory=PersistenceSpec)
    embeddings: EmbeddingSpec = field(default_factory=EmbeddingSpec)

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
            app_db=_credentials_from_env("DB_APP"),
            persistence=PersistenceSpec(backend=os.environ.get("DB_BACKEND") or DEFAULT_DB_BACKEND),
            embeddings=_embeddings_from_env(),
        )
