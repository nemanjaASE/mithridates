"""Errors the application raises. The API layer maps them to responses."""
from .models import QueryTrace


class ApplicationError(Exception):
    """Base class of the application's errors."""


class ConfigurationError(ApplicationError):
    """The process is configured in a way that cannot work. Raised at startup."""


class StoreUnavailable(ApplicationError):
    """The database cannot be reached. A rejected statement is not this error."""


class QueryExecutionError(ApplicationError):
    """The database rejected the query.

    Args:
        trace: The statement that was rejected.
    """

    def __init__(self, trace: QueryTrace) -> None:
        super().__init__("Query execution failed.")
        self.trace = trace


class InvalidTokenError(ApplicationError):
    """The token is missing, invalid, expired, or has the wrong issuer or audience."""
