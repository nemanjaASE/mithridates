"""Audit log on the standard `logging` module. Passwords and prompts are never logged."""
import logging
from collections.abc import Mapping

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

    def login_attempt(self, email: str, success: bool) -> None:
        """Logs a login attempt.

        Args:
            email: The submitted email, escaped before it is logged.
            success: Whether the login succeeded.
        """
        self._logger.info(
            "login_attempt email=%s success=%s", sanitize_for_log(email), success
        )

    def tool_call(self, tool: str, arguments: Mapping[str, object], outcome: str) -> None:
        # The arguments are written BY THE MODEL, so they are attacker-influenced input
        # and get the same treatment as a username: escaped and truncated.
        """Logs a tool call.

        Args:
            tool: The tool name.
            arguments: The arguments the model supplied, escaped before they are logged.
            outcome: The authorization decision.
        """
        rendered = ",".join(f"{k}={sanitize_for_log(str(v))}" for k, v in sorted(arguments.items()))
        self._logger.info(
            "tool_call tool=%s args=%s outcome=%s", sanitize_for_log(tool), rendered, outcome
        )
