"""Login endpoint. Statuses: 200 token issued, 401 rejected, 422 invalid input."""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ...application.use_cases import LoginUseCase
from ..schemas import ErrorOut, LoginIn, TokenOut
from .prefix import API_PREFIX

# Same message for an unknown email and a wrong password, so accounts cannot be enumerated.
_INVALID_CREDENTIALS = "Invalid email or password."


def build_auth_router(login_use_case: LoginUseCase) -> APIRouter:
    """Builds the router for `POST /auth/login`.

    Args:
        login_use_case: The use case that authenticates the user.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=API_PREFIX, tags=["auth"])

    @router.post(
        "/auth/login",
        response_model=TokenOut,
        responses={
            status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut, "description": "Login rejected"},
        },
    )
    def login(body: LoginIn) -> TokenOut | JSONResponse:
        """Authenticates the user and returns an access token."""
        outcome = login_use_case.execute(body.email, body.password)
        if outcome.access_token is None or outcome.user_id is None:
            error = ErrorOut(error=_INVALID_CREDENTIALS)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error.model_dump(exclude_none=True),
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenOut.from_domain(outcome.access_token, outcome.user_id)

    return router
