"""__TITLE__ demo: one feature in a vulnerable and a __safe__ variant.

- POST /api/v1/auth/login: an access token for a lab account.
- GET  /api/v1/users/me: the owner of the bearer token.
- POST /api/v1/{vulnerable|__safe__}/feature: the feature under attack.
"""
import logging

from fastapi import FastAPI

from .api.docs import register_docs
from .api.error_handlers import register_error_handlers
from .api.routers import (
    build_auth_router,
    build_feature_router,
    build_root_router,
    build_users_router,
)
from .api.security_headers import register_security_headers
from .api.startup import announce
from .config import Settings
from .container import Container, build_container

NAME = "__NAME__"
DESCRIPTION = """<img src="/logo.svg" alt="" width="72" align="right">

**__TITLE__.** One feature in a vulnerable and a __safe__ variant. Send the same payload
to both.

Deliberately vulnerable: keep it on `127.0.0.1`. The
[write-up](https://github.com/nemanjaASE/mithridates/blob/main/docs/writeups/__NN__-__SLUG__.md)
explains the attack and the fix.
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

    app = FastAPI(title=f"Mithridates · {NAME}", description=DESCRIPTION, docs_url=None)
    announce(NAME, container.settings.public_url)
    register_docs(app)
    register_security_headers(app)
    register_error_handlers(app)
    app.include_router(build_root_router())
    app.include_router(build_auth_router(container.login))
    app.include_router(build_users_router(container.get_current_user))
    app.include_router(build_feature_router(container.run_feature))
    return app
