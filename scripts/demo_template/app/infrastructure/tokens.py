"""Issues and verifies HS256 JWT access tokens."""
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

import jwt

from ..domain.errors import ConfigurationError, InvalidTokenError
from ..domain.models import AccessToken, Principal

_ALGORITHM = "HS256"
_REQUIRED_CLAIMS = ["exp", "iat", "nbf", "iss", "aud", "sub", "jti"]
_MIN_SECRET_BYTES = 32  # HS256 requires a key of at least 256 bits


@dataclass(frozen=True)
class JwtSettings:
    """Secret, lifetime, issuer and audience of the access tokens."""

    secret: str = field(repr=False)
    ttl_seconds: int = 900
    issuer: str = "__NAME__"
    audience: str = "__NAME__-api"

    def __post_init__(self) -> None:
        """Rejects a secret shorter than 32 bytes."""
        if len(self.secret.encode("utf-8")) < _MIN_SECRET_BYTES:
            raise ConfigurationError(f"JWT_SECRET must be at least {_MIN_SECRET_BYTES} bytes.")


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
            "sub": principal.username,
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
        return Principal(username=claims["sub"], role=claims.get("role", ""))
