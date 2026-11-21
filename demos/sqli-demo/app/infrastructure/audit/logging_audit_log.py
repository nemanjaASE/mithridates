"""Audit log on the standard `logging` module. Passwords are never logged."""
import logging

_MAX_LOGGED_LENGTH = 80


def sanitize_for_log(value: str) -> str:
    """Escapes line breaks and control characters so input cannot forge log lines.

    Args:
        value: The text to log.

    Returns:
        The escaped text.
    """
    escaped = value.encode("unicode_escape").decode("ascii")
    return escaped[:_MAX_LOGGED_LENGTH]


class LoggingAuditLog:
    """Writes security events to a logger.

    Args:
        logger: The logger to write to; defaults to the module's logger.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("security.audit")

    def login_attempt(self, variant: str, username: str, success: bool) -> None:
        """Logs a login attempt.

        Args:
            variant: The variant that handled the attempt.
            username: The submitted username, escaped before it is logged.
            success: Whether the login succeeded.
        """
        self._logger.info(
            "login_attempt variant=%s username=%s success=%s",
            variant,
            sanitize_for_log(username),
            success,
        )
