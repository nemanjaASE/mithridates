"""Verifies an email and password and issues an access token."""
from ...domain.entities import LoginOutcome
from ..ports import AuditLog, CredentialStore, PasswordHasher, TokenIssuer


class LoginUseCase:
    """Checks a password against its stored hash and issues a token. Audits every attempt.

    Args:
        credentials: Looks up credentials by email.
        hasher: Verifies the password.
        token_issuer: Issues the token.
        audit: Records the attempt.
    """

    def __init__(
        self,
        credentials: CredentialStore,
        hasher: PasswordHasher,
        token_issuer: TokenIssuer,
        audit: AuditLog,
    ) -> None:
        self._credentials = credentials
        self._hasher = hasher
        self._token_issuer = token_issuer
        self._audit = audit
        # Used when the email is unknown, so verification takes the same time either way
        # (no account enumeration via response timing).
        self._dummy_hash = hasher.hash("account-enumeration-placeholder")

    def execute(self, email: str, password: str) -> LoginOutcome:
        """Authenticates the user.

        Args:
            email: The submitted email.
            password: The submitted password.

        Returns:
            The token and user id, or a rejection that does not say why.
        """
        credential = self._credentials.find_credential(email)
        expected_hash = credential.password_hash if credential else self._dummy_hash
        password_ok = self._hasher.verify(password, expected_hash)
        authenticated = credential is not None and password_ok
        self._audit.login_attempt(email, authenticated)
        if credential is None or not password_ok:
            return LoginOutcome(access_token=None)
        return LoginOutcome(
            access_token=self._token_issuer.issue(credential.user_id),
            user_id=credential.user_id,
        )
