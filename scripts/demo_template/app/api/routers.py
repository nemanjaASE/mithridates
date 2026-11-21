"""HTTP routers. Each one is built by a factory that receives its use case.

Statuses: 200 success, 401 login rejected or missing token, 422 invalid input.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..application.use_cases import GetCurrentUserUseCase, LoginUseCase, RunFeatureUseCase
from ..domain.errors import InvalidTokenError
from ..domain.models import Variant
from .schemas import ErrorOut, FeatureIn, FeatureOut, LoginIn, PrincipalOut, TokenOut

API_PREFIX = "/api/v1"
_UNAUTHORIZED = {status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut, "description": "Missing or invalid token"}}
# The same message for an unknown user and a wrong password, so accounts cannot be enumerated.
_INVALID_CREDENTIALS = "Invalid username or password."

# auto_error=False: a missing token gets the same 401 as an invalid one.
_bearer = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _token(credentials: HTTPAuthorizationCredentials | None) -> str:
    """Returns the bearer token, or raises `InvalidTokenError` when there is none."""
    if credentials is None:
        raise InvalidTokenError()
    return credentials.credentials


def build_root_router() -> APIRouter:
    """Builds the router for `GET /`.

    Returns:
        The configured router.
    """
    router = APIRouter()

    @router.get("/")
    def root() -> dict:
        """Lists the available endpoints."""
        return {
            "lab": "__NAME__",
            "warning": "Deliberately vulnerable. Run locally, for education only.",
            "endpoints": [
                f"POST {API_PREFIX}/auth/login",
                f"GET {API_PREFIX}/users/me  (Authorization: Bearer <token>)",
                *(f"POST {API_PREFIX}/{v.value}/feature  (Authorization: Bearer <token>)" for v in Variant),
            ],
            "swagger": "/docs",
        }

    return router


def build_auth_router(login: LoginUseCase) -> APIRouter:
    """Builds the router for `POST /auth/login`.

    Args:
        login: The use case that authenticates the user.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=API_PREFIX, tags=["auth"])

    @router.post(
        "/auth/login",
        response_model=TokenOut,
        responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut, "description": "Login rejected"}},
    )
    def log_in(body: LoginIn) -> TokenOut | JSONResponse:
        """Authenticates the user and returns an access token."""
        token = login.execute(body.username, body.password)
        if token is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorOut(error=_INVALID_CREDENTIALS).model_dump(exclude_none=True),
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenOut.from_domain(token)

    return router


def build_users_router(get_current_user: GetCurrentUserUseCase) -> APIRouter:
    """Builds the router for `GET /users/me`.

    Args:
        get_current_user: The use case that resolves the token's owner.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=API_PREFIX, tags=["users"])

    @router.get("/users/me", response_model=PrincipalOut, responses=_UNAUTHORIZED)
    def me(credentials: BearerCredentials) -> PrincipalOut:
        """Returns the user the bearer token was issued for."""
        return PrincipalOut.from_domain(get_current_user.execute(_token(credentials)))

    return router


def build_feature_router(run_feature: RunFeatureUseCase) -> APIRouter:
    """Builds the router for `POST /{variant}/feature`.

    Args:
        run_feature: The use case that runs the feature.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=API_PREFIX, tags=["feature"])

    # TODO(attack): name the route after what the feature does, e.g. /{variant}/search.
    @router.post("/{variant}/feature", response_model=FeatureOut, responses=_UNAUTHORIZED)
    def feature(variant: Variant, body: FeatureIn, credentials: BearerCredentials) -> FeatureOut:
        """Runs the feature in the given variant for the token's owner."""
        return FeatureOut.from_domain(run_feature.execute(variant, body.input, _token(credentials)))

    return router
