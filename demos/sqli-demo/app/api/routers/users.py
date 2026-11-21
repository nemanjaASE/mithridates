from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...application.use_cases import GetCurrentUserUseCase
from ...domain.errors import InvalidTokenError
from ..schemas import ErrorOut, PrincipalOut
from .prefix import API_PREFIX

# auto_error=False: a missing token is handled by our handler (same 401 as a bad token).
_bearer = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def build_users_router(get_current_user: GetCurrentUserUseCase) -> APIRouter:
    """Builds the router for `GET /users/me`.

    Args:
        get_current_user: The use case that resolves the token's owner.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=API_PREFIX, tags=["users"])

    @router.get(
        "/users/me",
        response_model=PrincipalOut,
        responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut, "description": "Missing or invalid token"}},
    )
    def me(credentials: BearerCredentials) -> PrincipalOut:
        """Returns the user the bearer token was issued for."""
        if credentials is None:
            raise InvalidTokenError()
        return PrincipalOut.from_domain(get_current_user.execute(credentials.credentials))

    return router
