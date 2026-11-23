"""Prompt injection demo: an account assistant in a vulnerable and a mitigated variant.

- /api/v1/assistant/{variant}: account documents are in the model's context.
- /api/v1/agent/{variant}: the model fetches accounts through a tool.
"""
import logging

from fastapi import FastAPI

from .config import Settings
from .container import Container, build_container
from .presentation.docs import register_docs
from .presentation.error_handlers import register_error_handlers
from .presentation.middleware import register_security_headers
from .presentation.routers import (
    build_agent_router,
    build_assistant_router,
    build_auth_router,
    build_root_router,
)
from .presentation.security import build_current_user_id
from .presentation.startup import announce

NAME = "promptinj-demo"
DESCRIPTION = """<img src="/logo.svg" alt="" width="72" align="right">

**Prompt injection.** An account assistant and a tool-calling agent, each in a vulnerable
and a mitigated variant: in the vulnerable one the question decides whose data the model
sees, in the mitigated one the model sees only the verified user's data. Send the same
question to both.

Deliberately vulnerable: keep it on `127.0.0.1`. The
[write-up](https://github.com/nemanjaASE/mithridates/blob/main/docs/writeups/02-llm-prompt-injection.md)
explains the attack and the mitigations.
"""


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

    app = FastAPI(title=f"Mithridates · {NAME}", description=DESCRIPTION, docs_url=None)
    announce(NAME, settings.public_url)
    register_docs(app)
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
