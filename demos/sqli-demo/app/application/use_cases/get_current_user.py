from ...domain.models import Principal
from ...domain.ports import TokenVerifier


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
