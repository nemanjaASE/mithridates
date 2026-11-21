from typing import Protocol


class AuditLog(Protocol):
    """Records security events."""

    def login_attempt(self, variant: str, username: str, success: bool) -> None:
        """Records a login attempt.

        Args:
            variant: The variant that handled the attempt.
            username: The submitted username.
            success: Whether the login succeeded.
        """
