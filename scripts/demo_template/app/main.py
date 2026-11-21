"""__TITLE__ demo: one feature in a vulnerable and a __safe__ variant.

- POST /api/v1/auth/login: an access token for a lab account.
- GET  /api/v1/users/me: the owner of the bearer token.
- POST /api/v1/{vulnerable|__safe__}/feature: the feature under attack.
"""
import logging

from fastapi import FastAPI

from .api.error_handlers import register_error_handlers
from .api.routers import (
    build_auth_router,
    build_feature_router,
    build_root_router,
    build_users_router,
)
from .api.security_headers import register_security_headers
from .config import Settings
from .container import Container, build_container


def create_app(container: Container | None = None) -> FastAPI:
    """Creates the FastAPI application.

    Args:
        container: The wired use cases; built from the environment when omitted.

    Returns:
        The application.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    container = container or build_container(Settings.from_env())

    app = FastAPI(title="__NAME__", description="Deliberately vulnerable lab: __TITLE__ and its fix.")
    register_security_headers(app)
    register_error_handlers(app)
    app.include_router(build_root_router())
    app.include_router(build_auth_router(container.login))
    app.include_router(build_users_router(container.get_current_user))
    app.include_router(build_feature_router(container.run_feature))
    return app
