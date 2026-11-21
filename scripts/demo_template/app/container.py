"""Composition root: wires the adapters to the use cases."""
from dataclasses import dataclass

from .application.use_cases import GetCurrentUserUseCase, LoginUseCase, RunFeatureUseCase
from .config import Settings
from .domain.models import Variant
from .domain.ports import Feature
from .infrastructure.accounts import LabAccounts
from .infrastructure.audit import LoggingAuditLog
# [postgres]
from .infrastructure.database import PostgresDatabase
# [/postgres]
from .infrastructure.feature import __Safe__Feature, VulnerableFeature
from .infrastructure.tokens import JwtTokenService


@dataclass(frozen=True)
class Container:
    """The use cases the HTTP layer needs."""

    login: LoginUseCase
    get_current_user: GetCurrentUserUseCase
    run_feature: RunFeatureUseCase


def build_container(settings: Settings) -> Container:
    """Creates the adapters and the use cases.

    Args:
        settings: The application settings.

    Returns:
        The wired use cases.
    """
    tokens = JwtTokenService(settings.jwt)
    # [postgres]
    db = PostgresDatabase(settings.server, settings.app_db)
    features: dict[Variant, Feature] = {
        Variant.VULNERABLE: VulnerableFeature(db),
        Variant.__SAFE__: __Safe__Feature(db),
    }
    # [/postgres]
    # [no-postgres]
    features: dict[Variant, Feature] = {
        Variant.VULNERABLE: VulnerableFeature(),
        Variant.__SAFE__: __Safe__Feature(),
    }
    # [/no-postgres]
    return Container(
        login=LoginUseCase(LabAccounts(), tokens, LoggingAuditLog()),
        get_current_user=GetCurrentUserUseCase(tokens),
        run_feature=RunFeatureUseCase(features, tokens),
    )
