from dataclasses import dataclass

from .access_token import AccessToken
from .query_trace import QueryTrace


@dataclass(frozen=True)
class LoginOutcome:
    """Result of a login: the issued token, or None, and the executed SQL."""

    access_token: AccessToken | None  # None -> login rejected
    trace: QueryTrace

    @property
    def succeeded(self) -> bool:
        """Whether a token was issued."""
        return self.access_token is not None
