"""Authentication dependency: the user id comes only from the verified JWT."""
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..application.errors import InvalidTokenError
from ..application.ports import TokenVerifier

_bearer = HTTPBearer(auto_error=False)


def build_current_user_id(verifier: TokenVerifier) -> Callable[..., str]:
    """Builds the dependency that returns the authenticated user id.

    Args:
        verifier: Verifies tokens.

    Returns:
        The dependency.
    """
    def _current_user_id(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> str:
        """Returns the user id from the bearer token.

        Raises:
            InvalidTokenError: The token is missing, invalid or expired.
        """
        if credentials is None:
            raise InvalidTokenError()
        return verifier.subject_of(credentials.credentials)

    return _current_user_id
