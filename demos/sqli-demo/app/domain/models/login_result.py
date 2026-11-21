from dataclasses import dataclass

from .query_trace import QueryTrace
from .user import User


@dataclass(frozen=True)
class LoginResult:
    """Result of a credential check: the matching users and the executed SQL."""

    authenticated: bool
    users: tuple[User, ...]
    trace: QueryTrace
