"""Audit log on the standard `logging` module. Passwords are never logged."""
import logging


def sanitize_for_log(value: str) -> str:
    """Escapes line breaks and control characters so input cannot forge log lines.

    Args:
        value: The text to log.

    Returns:
        The escaped text.
    """
    return "".join(ch if ch.isprintable() else repr(ch)[1:-1] for ch in value)


class LoggingAuditLog:
    """Writes security events to a logger.

    Args:
        logger: The logger to write to; defaults to the module's logger.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("app.audit")

    def login_attempt(self, username: str, success: bool) -> None:
        """Logs a login attempt.

        Args:
            username: The submitted username, escaped before it is logged.
            success: Whether the login succeeded.
        """
        self._logger.info("login_attempt username=%s success=%s", sanitize_for_log(username), success)
