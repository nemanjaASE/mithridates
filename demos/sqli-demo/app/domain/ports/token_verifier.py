from typing import Protocol

from ..models import Principal


class TokenVerifier(Protocol):
    """Verifies access tokens."""

    def verify(self, token: str) -> Principal:
        """Verifies a token.

        Args:
            token: The bearer token.

        Returns:
            The user the token was issued for.

        Raises:
            InvalidTokenError: The token is invalid or expired.
        """
