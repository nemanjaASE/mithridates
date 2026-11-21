"""Composition root: wires the adapters to the use cases."""
from dataclasses import dataclass

from .application.use_cases import GetCurrentUserUseCase, InspectLabDataUseCase, LoginUseCase
from .config import Settings
from .domain.models import Variant
from .infrastructure.audit import LoggingAuditLog
from .infrastructure.auth import SafeSqlAuthenticator, VulnerableSqlAuthenticator
from .infrastructure.persistence import PostgresDatabase, PostgresLabInspector
from .infrastructure.tokens import JwtTokenService


@dataclass(frozen=True)
class Container:
    """The use cases the HTTP layer needs."""

    settings: Settings
    login: dict[Variant, LoginUseCase]
    get_current_user: GetCurrentUserUseCase
    inspect_lab: InspectLabDataUseCase


def build_container(settings: Settings) -> Container:
    """Creates the adapters and the use cases.

    Args:
        settings: The application settings.

    Returns:
        The wired use cases.
    """
    legacy_db = PostgresDatabase(settings.server, settings.legacy_db)
    app_db = PostgresDatabase(settings.server, settings.app_db)
    audit = LoggingAuditLog()
    tokens = JwtTokenService(settings.jwt)

    # A new variant (e.g. a "blacklist" filter) = a new adapter + one line here (Open/Closed).
    authenticators = {
        Variant.VULNERABLE: VulnerableSqlAuthenticator(legacy_db),
        Variant.SAFE: SafeSqlAuthenticator(app_db),
    }
    return Container(
        settings=settings,
        login={v: LoginUseCase(v, a, tokens, audit) for v, a in authenticators.items()},
        get_current_user=GetCurrentUserUseCase(tokens),
        inspect_lab=InspectLabDataUseCase(PostgresLabInspector(legacy_db)),
    )
