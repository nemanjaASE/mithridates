"""SQL injection demo: a login endpoint in a vulnerable and a safe variant.

- POST /api/v1/vulnerable/auth/login: the query is built by string formatting.
- POST /api/v1/safe/auth/login: the query is parameterized.
- GET  /api/v1/users/me: the owner of the bearer token.
- GET  /api/v1/debug/users: the database contents, when ENABLE_DEBUG_ENDPOINTS is on.
"""
import logging

from fastapi import FastAPI

from .api.error_handlers import register_error_handlers
from .api.middleware import register_security_headers
from .api.routers import (
    build_auth_router,
    build_debug_router,
    build_root_router,
    build_users_router,
)
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
    settings = container.settings

    app = FastAPI(
        title="SQLi Demo Lab",
        description="Controlled lab demonstrating a SQL injection attack and its fix.",
    )
    register_security_headers(app)
    register_error_handlers(app, settings.expose_query_trace)
    app.include_router(build_root_router(debug_enabled=settings.enable_debug_endpoints))
    app.include_router(build_auth_router(container.login, settings.expose_query_trace))
    app.include_router(build_users_router(container.get_current_user))
    if settings.enable_debug_endpoints:
        app.include_router(build_debug_router(container.inspect_lab))
    return app
