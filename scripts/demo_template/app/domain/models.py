"""Domain models."""
from dataclasses import dataclass, field
from enum import Enum


class Variant(str, Enum):
    """The implementation variants: vulnerable and __safe__."""

    VULNERABLE = "vulnerable"
    __SAFE__ = "__safe__"


@dataclass(frozen=True)
class Principal:
    """The user an access token was issued for."""

    username: str
    role: str


@dataclass(frozen=True)
class AccessToken:
    """An issued access token and its lifetime in seconds."""

    value: str = field(repr=False)  # a credential: it must not reach the log through repr()
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class FeatureResult:
    """What the feature under attack returns."""

    result: str
