"""Errors the application raises. The presentation layer maps them to responses."""


class ApplicationError(Exception):
    """Base class of the application's errors."""


class ConfigurationError(ApplicationError):
    """The process is configured in a way that cannot work. Raised at startup."""


class UnknownAssistant(ApplicationError):
    """No assistant is registered under the given name.

    Args:
        name: The requested name.
        known: The registered names.
    """

    def __init__(self, name: str, known: tuple[str, ...] = ()) -> None:
        super().__init__(f"Unknown assistant {name!r}. Known: {', '.join(known) or 'none'}.")
        self.name = name
        self.known = known


class UnknownTool(ApplicationError):
    """The model asked for a tool that is not registered.

    Args:
        name: The requested tool name.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown tool {name!r}.")
        self.name = name


class StoreUnavailable(ApplicationError):
    """The data store cannot be reached. A malformed query is not this error."""


class InvalidInput(ApplicationError):
    """A use case received input it cannot process."""


class InvalidTokenError(ApplicationError):
    """The access token is missing, malformed, expired or wrongly signed."""


class LanguageModelUnavailable(ApplicationError):
    """The model cannot be reached, timed out, or exceeded its step limit."""
