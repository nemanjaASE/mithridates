"""Prompt injection demo: an account assistant in a vulnerable and a mitigated variant.

- /api/v1/assistant/{variant}: account documents are in the model's context.
- /api/v1/agent/{variant}: the model fetches accounts through a tool.
"""
import logging

from fastapi import FastAPI

from .config import Settings
from .container import Container, build_container
from .presentation.error_handlers import register_error_handlers
from .presentation.middleware import register_security_headers
from .presentation.routers import (
    build_agent_router,
    build_assistant_router,
    build_auth_router,
    build_root_router,
)
from .presentation.security import build_current_user_id


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

    app = FastAPI(title="Prompt Injection Demo Lab")
    register_security_headers(app)
    register_error_handlers(app)
    current_user_id = build_current_user_id(container.jwt_service)

    app.include_router(build_root_router(container.backend, container.assistants))
    app.include_router(build_auth_router(container.login_use_case))
    app.include_router(
        build_assistant_router(
            container.ask_use_case,
            current_user_id,
            expose_prompt_trace=settings.expose_prompt_trace,
            expose_raw_output=settings.expose_raw_output,
        )
    )
    app.include_router(
        build_agent_router(
            container.ask_use_case,
            current_user_id,
            expose_tool_trace=settings.expose_prompt_trace,
        )
    )
    return app
