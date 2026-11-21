from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    """The user an access token was issued for."""

    user_id: str
    username: str
    role: str
