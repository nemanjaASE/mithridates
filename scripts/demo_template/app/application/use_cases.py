"""Use cases: log in, resolve the token's owner, run the feature."""
from collections.abc import Mapping

from ..domain.models import AccessToken, FeatureResult, Principal, Variant
from ..domain.ports import AuditLog, CredentialChecker, Feature, TokenIssuer, TokenVerifier


class LoginUseCase:
    """Checks credentials and issues an access token. Audits every attempt.

    Args:
        credentials: Checks the username and password.
        token_issuer: Issues the token.
        audit: Records the attempt.
    """

    def __init__(self, credentials: CredentialChecker, token_issuer: TokenIssuer, audit: AuditLog) -> None:
        self._credentials = credentials
        self._token_issuer = token_issuer
        self._audit = audit

    def execute(self, username: str, password: str) -> AccessToken | None:
        """Authenticates the user.

        Args:
            username: The submitted username.
            password: The submitted password.

        Returns:
            The token, or None when the login is rejected.
        """
        principal = self._credentials.check(username, password)
        self._audit.login_attempt(username, principal is not None)
        return None if principal is None else self._token_issuer.issue(principal)


class GetCurrentUserUseCase:
    """Resolves the owner of an access token.

    Args:
        verifier: Verifies tokens.
    """

    def __init__(self, verifier: TokenVerifier) -> None:
        self._verifier = verifier

    def execute(self, token: str) -> Principal:
        """Returns the token's owner.

        Args:
            token: The bearer token.

        Returns:
            The authenticated user.

        Raises:
            InvalidTokenError: The token is invalid or expired.
        """
        return self._verifier.verify(token)


class RunFeatureUseCase:
    """Runs one variant of the feature for the token's owner.

    Args:
        features: The implementation of each variant.
        verifier: Verifies tokens.
    """

    def __init__(self, features: Mapping[Variant, Feature], verifier: TokenVerifier) -> None:
        self._features = features
        self._verifier = verifier

    def execute(self, variant: Variant, value: str, token: str) -> FeatureResult:
        """Runs the feature.

        Args:
            variant: The implementation to use.
            value: The input the user submitted.
            token: The bearer token.

        Returns:
            The feature's result.

        Raises:
            InvalidTokenError: The token is invalid or expired.
        """
        principal = self._verifier.verify(token)
        return self._features[variant].run(value, principal)
