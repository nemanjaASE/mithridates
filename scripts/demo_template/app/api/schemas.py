"""Request and response models of the HTTP API. Every input has a bounded length."""
from pydantic import BaseModel, Field

from ..domain.models import AccessToken, FeatureResult, Principal


class LoginIn(BaseModel):
    """Credentials submitted to the login endpoint."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    """Response of a successful login: the access token and its lifetime."""

    access_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_domain(cls, token: AccessToken) -> TokenOut:
        """Builds the response from an access token."""
        return cls(access_token=token.value, token_type=token.token_type, expires_in=token.expires_in)


class PrincipalOut(BaseModel):
    """Response of `GET /users/me`: the token's owner."""

    username: str
    role: str

    @classmethod
    def from_domain(cls, principal: Principal) -> PrincipalOut:
        """Builds the response from a principal."""
        return cls(username=principal.username, role=principal.role)


class FeatureIn(BaseModel):
    """Input of the feature under attack."""

    input: str = Field(min_length=1, max_length=500)


class FeatureOut(BaseModel):
    """Output of the feature under attack."""

    result: str

    @classmethod
    def from_domain(cls, result: FeatureResult) -> FeatureOut:
        """Builds the response from the feature's result."""
        return cls(result=result.result)


class ErrorOut(BaseModel):
    """Error response: a generic message and, where useful, the id to find it in the log."""

    error: str
    error_id: str | None = None
