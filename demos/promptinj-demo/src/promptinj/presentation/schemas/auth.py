"""Login request and token response models."""
from pydantic import BaseModel, Field

from ...domain.entities import AccessToken

MAX_INPUT_LENGTH = 128


class LoginIn(BaseModel):
    """Credentials submitted to the login endpoint, with bounded lengths."""

    email: str = Field(min_length=1, max_length=MAX_INPUT_LENGTH)
    password: str = Field(min_length=1, max_length=MAX_INPUT_LENGTH)


class TokenOut(BaseModel):
    """Response of a successful login: the access token, its lifetime and the user id."""

    access_token: str
    token_type: str
    expires_in: int
    user_id: str

    @classmethod
    def from_domain(cls, token: AccessToken, user_id: str) -> TokenOut:
        """Builds the response from an access token.

        Args:
            token: The issued token.
            user_id: The user the token was issued for.

        Returns:
            The response model.
        """
        return cls(
            access_token=token.value,
            token_type=token.token_type,
            expires_in=token.expires_in,
            user_id=user_id,
        )
