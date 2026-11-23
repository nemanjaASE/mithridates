from pydantic import BaseModel

from ...domain.models import AccessToken
from .trace import DebugTraceOut


class TokenOut(BaseModel):
    """Response of a successful login: the access token and its lifetime."""

    access_token: str
    token_type: str
    expires_in: int
    debug: DebugTraceOut | None = None

    @classmethod
    def from_domain(cls, token: AccessToken, debug: DebugTraceOut | None) -> TokenOut:
        """Builds the response from an access token.

        Args:
            token: The issued token.
            debug: The executed SQL, or None when the trace is off.

        Returns:
            The response model.
        """
        return cls(
            access_token=token.value,
            token_type=token.token_type,
            expires_in=token.expires_in,
            debug=debug,
        )
