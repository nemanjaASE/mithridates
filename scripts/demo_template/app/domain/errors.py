"""Errors the application raises. The API layer maps them to responses."""


class ApplicationError(Exception):
    """Base class of the application's errors."""


class ConfigurationError(ApplicationError):
    """The process is configured in a way that cannot work. Raised at startup."""


class InvalidTokenError(ApplicationError):
    """The token is missing, invalid or expired."""


class StoreUnavailable(ApplicationError):
    """A dependency of the feature, such as a database, cannot be reached."""
