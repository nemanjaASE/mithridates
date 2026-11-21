"""Domain entities and result objects. Standard library only."""
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class Variant(str, Enum):
    """The implementation variants: vulnerable and mitigated."""

    VULNERABLE = "vulnerable"
    MITIGATED = "mitigated"


@dataclass(frozen=True)
class Account:
    """A customer account. `card_number` is the full card number and is sensitive."""

    id: str
    name: str
    email: str
    plan: str
    balance_rsd: int
    card_number: str  # full PAN; never to be shown in full

    @property
    def card_last4(self) -> str:
        """The last four digits of the card number."""
        digits = "".join(c for c in self.card_number if c.isdigit())
        return digits[-4:]


@dataclass(frozen=True)
class Credential:
    """A login credential: account id, email and password hash."""

    user_id: str
    email: str
    password_hash: str = field(repr=False)  # keep the hash out of logs via repr()


@dataclass(frozen=True)
class AccessToken:
    """An issued access token, its type and its lifetime in seconds."""

    value: str = field(repr=False)  # the token is a credential — must not reach the log via repr()
    token_type: str = "Bearer"
    expires_in: int = 900


@dataclass(frozen=True)
class LoginOutcome:
    """Result of a login: the token and user id, or None. A rejection has no reason."""

    access_token: AccessToken | None
    user_id: str | None = None

    @property
    def succeeded(self) -> bool:
        """Whether a token was issued."""
        return self.access_token is not None


@dataclass(frozen=True)
class RetrievedChunk:
    """A retrieved document: its owner, its text and its similarity score."""

    owner_id: str
    text: str
    score: float = 0.0


@dataclass(frozen=True)
class Prompt:
    """The system prompt and user message sent to the model."""

    system: str
    user: str


@dataclass(frozen=True)
class AccountLookupResult:
    """Result of an account lookup: the account, or a refusal."""

    authorized: bool
    content: str


class ToolOutcome(str, Enum):
    """Outcome of a tool call the model requested.

    AUTHORIZED    the tool ran and the policy allowed the call.
    DENIED        the tool ran and the policy refused the call.
    NOT_EXECUTED  the call never reached the tool: no budget left, an unknown tool name,
                  or arguments that failed validation.
    """

    AUTHORIZED = "authorized"
    DENIED = "denied"
    NOT_EXECUTED = "not-executed"


@dataclass(frozen=True)
class ToolInvocation:
    """A tool call the model made: the tool, the arguments as sent, and the outcome."""

    tool: str
    arguments: Mapping[str, object]
    outcome: ToolOutcome

    @property
    def authorized(self) -> bool:
        """Whether the policy allowed the call."""
        return self.outcome is ToolOutcome.AUTHORIZED

    @property
    def executed(self) -> bool:
        """Whether the call reached the tool. Only these count against the budget."""
        return self.outcome in (ToolOutcome.AUTHORIZED, ToolOutcome.DENIED)


@dataclass(frozen=True)
class RetrievalFacts:
    """How the context was assembled: counts, owners and settings, never document text."""

    documents: int = 0
    scoped_to_owner: bool = False
    safe_fields: bool = False
    owners: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssistantAnswer:
    """Result of any assistant: the answer and what produced it.

    `raw_output` is the model's output before the output check; `answer` is what the caller
    receives. They differ when `block_reason` is set.
    """

    variant: Variant
    answer: str
    raw_output: str
    block_reason: str | None = None
    prompt: Prompt | None = None
    retrieval: RetrievalFacts | None = None
    tool_invocations: tuple[ToolInvocation, ...] = ()

    @property
    def blocked(self) -> bool:
        """Whether the output check blocked the answer."""
        return self.block_reason is not None
