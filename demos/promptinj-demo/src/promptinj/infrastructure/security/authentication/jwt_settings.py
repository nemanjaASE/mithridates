from dataclasses import dataclass, field

# HS256 requires a key of at least 256 bits.
_MIN_SECRET_BYTES = 32


@dataclass(frozen=True)
class JwtSettings:
    """Secret, lifetime, issuer and audience of the access tokens."""

    secret: str = field(repr=False)
    ttl_seconds: int = 900  # short lifetime: a stolen token expires quickly
    issuer: str = "promptinj-demo"
    audience: str = "promptinj-demo-api"

    def __post_init__(self) -> None:
        """Rejects a secret shorter than 32 bytes."""
        if len(self.secret.encode("utf-8")) < _MIN_SECRET_BYTES:
            raise ValueError(f"JWT secret must be at least {_MIN_SECRET_BYTES} bytes.")
