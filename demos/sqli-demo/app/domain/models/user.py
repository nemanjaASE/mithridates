from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """A user row as returned by the authentication query."""

    id: str  # GUID (UUIDv7) as text
    username: str
    role: str
