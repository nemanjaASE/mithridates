from typing import Protocol

from ..models import AccessToken, Principal


class TokenIssuer(Protocol):
    """Issues access tokens."""

    def issue(self, principal: Principal) -> AccessToken:
        """Issues a token for a user.

        Args:
            principal: The authenticated user.

        Returns:
            The access token.
        """
