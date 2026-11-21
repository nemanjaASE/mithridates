"""Issues and verifies HS256 JWT access tokens. The `sub` claim is the user id."""
import time
import uuid
from collections.abc import Callable

import jwt

from ....application.errors import InvalidTokenError
from ....domain.entities import AccessToken
from .jwt_settings import JwtSettings

_ALGORITHM = "HS256"
_REQUIRED_CLAIMS = ["exp", "iat", "nbf", "iss", "aud", "sub"]


class JwtService:
    """Issues and verifies access tokens.

    Args:
        settings: Secret, lifetime, issuer and audience.
        clock: Returns the current time in seconds.
    """

    def __init__(self, settings: JwtSettings, clock: Callable[[], float] = time.time) -> None:
        self._settings = settings
        self._clock = clock

    def issue(self, subject: str) -> AccessToken:
        """Issues a token.

        Args:
            subject: The user id.

        Returns:
            The signed access token.
        """
        now = int(self._clock())
        claims = {
            "sub": subject,
            "iss": self._settings.issuer,
            "aud": self._settings.audience,
            "iat": now,
            "nbf": now,
            "exp": now + self._settings.ttl_seconds,
            "jti": uuid.uuid4().hex,
        }
        value = jwt.encode(claims, self._settings.secret, algorithm=_ALGORITHM)
        return AccessToken(value=value, token_type="Bearer", expires_in=self._settings.ttl_seconds)

    def subject_of(self, token: str) -> str:
        """Verifies the signature and the claims of a token.

        Args:
            token: The bearer token.

        Returns:
            The user id.

        Raises:
            InvalidTokenError: The token is invalid or expired.
        """
        try:
            claims = jwt.decode(
                token,
                self._settings.secret,
                algorithms=[_ALGORITHM],
                audience=self._settings.audience,
                issuer=self._settings.issuer,
                options={"require": _REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError() from exc
        return claims["sub"]
