"""Ports implemented by the infrastructure. Both variants implement the same `Feature`."""
from typing import Protocol

from .models import AccessToken, FeatureResult, Principal


class Feature(Protocol):
    """The feature under attack. The vulnerable and the __safe__ adapter implement it."""

    def run(self, value: str, principal: Principal) -> FeatureResult:
        """Runs the feature.

        Args:
            value: The input the user submitted.
            principal: The authenticated user.

        Returns:
            The feature's result.
        """


class CredentialChecker(Protocol):
    """Checks a username and password."""

    def check(self, username: str, password: str) -> Principal | None:
        """Checks the credentials.

        Args:
            username: The submitted username.
            password: The submitted password.

        Returns:
            The user, or None when the credentials do not match.
        """


class TokenIssuer(Protocol):
    """Issues access tokens."""

    def issue(self, principal: Principal) -> AccessToken:
        """Issues a token for a user.

        Args:
            principal: The authenticated user.

        Returns:
            The access token.
        """


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


class AuditLog(Protocol):
    """Records security events."""

    def login_attempt(self, username: str, success: bool) -> None:
        """Records a login attempt.

        Args:
            username: The submitted username.
            success: Whether the login succeeded.
        """
