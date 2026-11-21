"""Login endpoint: 200 token issued, 401 rejected, 400 query failed, 422 invalid input."""
from collections.abc import Mapping

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ...application.use_cases import LoginUseCase
from ...domain.models import Variant
from ..schemas import DebugTraceOut, ErrorOut, LoginIn, TokenOut
from .prefix import API_PREFIX

# Same message for an unknown user and a wrong password, so accounts cannot be enumerated.
_INVALID_CREDENTIALS = "Invalid username or password."


def build_auth_router(login_use_cases: Mapping[Variant, LoginUseCase], expose_query_trace: bool) -> APIRouter:
    """Builds the router for `POST /{variant}/auth/login`.

    Args:
        login_use_cases: The login use case for each variant.
        expose_query_trace: Whether the executed SQL is included in the response.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=API_PREFIX, tags=["auth"])

    @router.post(
        "/{variant}/auth/login",
        response_model=TokenOut,
        response_model_exclude_none=True,
        responses={
            status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut, "description": "Login rejected"},
            status.HTTP_400_BAD_REQUEST: {"model": ErrorOut, "description": "Request could not be processed"},
        },
    )
    def login(variant: Variant, body: LoginIn) -> TokenOut | JSONResponse:
        """Authenticates the user and returns an access token."""
        outcome = login_use_cases[variant].execute(body.username, body.password)
        debug = DebugTraceOut.from_trace(outcome.trace, expose_query_trace)
        if outcome.access_token is None:
            error = ErrorOut(error=_INVALID_CREDENTIALS, debug=debug)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error.model_dump(exclude_none=True),
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenOut.from_domain(outcome.access_token, debug)

    return router
