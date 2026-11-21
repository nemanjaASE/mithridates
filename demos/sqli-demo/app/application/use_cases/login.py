from ...domain.models import LoginOutcome, Principal, Variant
from ...domain.ports import AuditLog, Authenticator, TokenIssuer


class LoginUseCase:
    """Checks credentials and issues a token for the first user the database returns.

    Args:
        variant: The variant this use case serves.
        authenticator: Checks the credentials.
        token_issuer: Issues the access token.
        audit: Records the login attempt.
    """

    def __init__(
        self,
        variant: Variant,
        authenticator: Authenticator,
        token_issuer: TokenIssuer,
        audit: AuditLog,
    ) -> None:
        self._variant = variant
        self._authenticator = authenticator
        self._token_issuer = token_issuer
        self._audit = audit

    def execute(self, username: str, password: str) -> LoginOutcome:
        """Authenticates the user and issues an access token.

        Args:
            username: The submitted username.
            password: The submitted password.

        Returns:
            The token, or None when the login is rejected, and the executed SQL.
        """
        result = self._authenticator.authenticate(username, password)
        self._audit.login_attempt(self._variant.value, username, result.authenticated)
        if not result.authenticated:
            return LoginOutcome(access_token=None, trace=result.trace)

        user = result.users[0]
        principal = Principal(user_id=str(user.id), username=user.username, role=user.role)
        return LoginOutcome(access_token=self._token_issuer.issue(principal), trace=result.trace)
