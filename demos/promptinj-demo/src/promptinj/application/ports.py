"""Protocols for everything the application needs from the infrastructure."""
from collections.abc import Mapping
from typing import Protocol

from ..domain.entities import (
    AccessToken,
    Account,
    AccountLookupResult,
    AssistantAnswer,
    Credential,
    RetrievedChunk,
)


class AccountRepository(Protocol):
    """Reads account records. Makes no access decisions."""

    def get(self, account_id: str) -> Account | None:
        """Returns an account by id.

        Args:
            account_id: The account id.

        Returns:
            The account, or None if it does not exist.
        """


class CredentialStore(Protocol):
    """Looks up login credentials. Only password hashes are stored."""

    def find_credential(self, email: str) -> Credential | None:
        """Returns the credential for an email address.

        Args:
            email: The login email.

        Returns:
            The credential, or None if the email is unknown.
        """


class DocumentRetriever(Protocol):
    """Retrieves the documents most similar to a question."""

    def retrieve(
        self, query: str, k: int, owner_id: str | None, *, safe_fields: bool = False
    ) -> list[RetrievedChunk]:
        """Returns the k most similar documents.

        Args:
            query: The question.
            k: The number of documents to return.
            owner_id: Restricts the search to one owner; None searches every owner.
            safe_fields: Returns only the allow-listed fields of each document.

        Returns:
            The documents, most similar first.
        """


class DocumentSearch(Protocol):
    """Nearest-neighbour search over the stored document vectors."""

    def nearest(
        self, vector: list[float], k: int, owner_id: str | None, *, safe_fields: bool = False
    ) -> list[RetrievedChunk]:
        """Returns the k documents nearest to a vector.

        Args:
            vector: The query vector.
            k: The number of documents to return.
            owner_id: Restricts the search to one owner; None searches every owner.
            safe_fields: Returns only the allow-listed fields of each document.

        Returns:
            The documents, nearest first.
        """


class Embedder(Protocol):
    """Turns text into vectors. Documents and queries must use the same model."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embeds several texts.

        Args:
            texts: The texts to embed.

        Returns:
            One vector per text.
        """

    def embed_query(self, text: str) -> list[float]:
        """Embeds one query.

        Args:
            text: The query.

        Returns:
            The vector.
        """


class AccountLookupTool(Protocol):
    """Looks up one account by id and decides whether the caller may see it."""

    def lookup(self, account_id: str) -> AccountLookupResult:
        """Looks up an account.

        Args:
            account_id: The id the model asked for.

        Returns:
            The account, or the reason the lookup was refused.
        """


class OutputFilter(Protocol):
    """Checks a model's answer before it is returned."""

    def inspect(self, text: str) -> str | None:
        """Checks the answer.

        Args:
            text: The model's answer.

        Returns:
            The reason to block it, or None if it may be returned.
        """


class PasswordHasher(Protocol):
    """Hashes and verifies passwords."""

    def hash(self, password: str) -> str:
        """Hashes a password.

        Args:
            password: The plaintext password.

        Returns:
            The hash.
        """

    def verify(self, password: str, password_hash: str) -> bool:
        """Checks a password against a hash.

        Args:
            password: The plaintext password.
            password_hash: The stored hash.

        Returns:
            Whether they match.
        """


class TokenIssuer(Protocol):
    """Issues access tokens."""

    def issue(self, subject: str) -> AccessToken:
        """Issues a token.

        Args:
            subject: The user id.

        Returns:
            The access token.
        """


class TokenVerifier(Protocol):
    """Verifies access tokens."""

    def subject_of(self, token: str) -> str:
        """Verifies a token and returns its subject.

        Args:
            token: The bearer token.

        Returns:
            The user id.

        Raises:
            InvalidTokenError: The token is invalid or expired.
        """


class AuditLog(Protocol):
    """Records security events. Implementations escape input before writing it."""

    def login_attempt(self, email: str, success: bool) -> None:
        """Records a login attempt.

        Args:
            email: The submitted email.
            success: Whether the login succeeded.
        """

    def tool_call(self, tool: str, arguments: Mapping[str, object], outcome: str) -> None:
        """Records a tool call the model made.

        Args:
            tool: The tool name.
            arguments: The arguments the model supplied.
            outcome: The authorization decision.
        """


class Assistant(Protocol):
    """Answers a question on behalf of an authenticated user."""

    def answer(self, question: str, current_user_id: str) -> AssistantAnswer:
        """Answers a question.

        Args:
            question: The user's question.
            current_user_id: The user id from the verified token.

        Returns:
            The answer and its trace.
        """


class AssistantRegistry(Protocol):
    """Resolves assistants by name."""

    def get(self, name: str) -> Assistant:
        """Returns an assistant.

        Args:
            name: The assistant name.

        Returns:
            The assistant.

        Raises:
            UnknownAssistant: No assistant has that name.
        """

    def describe(self) -> Mapping[str, str]:
        """Describes the registered assistants.

        Returns:
            A short description of each assistant, by name.
        """
