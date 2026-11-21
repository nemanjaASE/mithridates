from dataclasses import dataclass, field


@dataclass(frozen=True)
class AccessToken:
    """An issued access token and its lifetime in seconds."""

    value: str = field(repr=False)  # the token is a credential — must not reach the log via repr()
    token_type: str
    expires_in: int
