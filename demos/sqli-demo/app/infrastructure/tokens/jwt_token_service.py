"""Issues and verifies HS256 JWT access tokens."""
import time
import uuid
from collections.abc import Callable

import jwt

from ...domain.errors import InvalidTokenError
from ...domain.models import AccessToken, Principal
from .jwt_settings import JwtSettings

_ALGORITHM = "HS256"
_REQUIRED_CLAIMS = ["exp", "iat", "nbf", "iss", "aud", "sub"]


class JwtTokenService:
    """Issues and verifies access tokens.

    Args:
        settings: Secret, lifetime, issuer and audience.
        clock: Returns the current time in seconds.
    """

    def __init__(self, settings: JwtSettings, clock: Callable[[], float] = time.time) -> None:
        self._settings = settings
        self._clock = clock

    def issue(self, principal: Principal) -> AccessToken:
        """Issues a token for a user.

        Args:
            principal: The authenticated user.

        Returns:
            The signed access token.
        """
        now = int(self._clock())
        claims = {
            "sub": principal.user_id,
            "username": principal.username,
            "role": principal.role,
            "iss": self._settings.issuer,
            "aud": self._settings.audience,
            "iat": now,
            "nbf": now,
            "exp": now + self._settings.ttl_seconds,
            "jti": uuid.uuid4().hex,
        }
        value = jwt.encode(claims, self._settings.secret, algorithm=_ALGORITHM)
        return AccessToken(value=value, token_type="Bearer", expires_in=self._settings.ttl_seconds)

    def verify(self, token: str) -> Principal:
        """Verifies the signature and the claims of a token.

        Args:
            token: The bearer token.

        Returns:
            The user the token was issued for.

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
        return Principal(user_id=claims["sub"], username=claims.get("username"), role=claims.get("role"))
