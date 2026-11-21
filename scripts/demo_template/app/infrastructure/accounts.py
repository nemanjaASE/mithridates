"""The lab accounts. Fixed, fictional values; only bcrypt hashes of the passwords are kept."""
import bcrypt

from ..domain.models import Principal

# username -> (role, bcrypt hash). The passwords are listed in the README.
_ACCOUNTS = {
    "ana": ("user", "$2b$12$TkJMPMmToLhBRx8zKgZUS.ccAqca1aFCe.1nZ5cb7oe5tHFSjfSim"),
    "admin": ("admin", "$2b$12$2BJEH9lkZxyb8EbEIk.sNuFlCgqQXyDRmJOjj7KNt.OfTzOVSM.nG"),
}
# Checked when the username is unknown, so the response time does not reveal which exist.
_UNKNOWN = ("", _ACCOUNTS["ana"][1])


class LabAccounts:
    """Checks credentials against the fixed lab accounts."""

    def check(self, username: str, password: str) -> Principal | None:
        """Checks the credentials in constant time.

        Args:
            username: The submitted username.
            password: The submitted password.

        Returns:
            The user, or None when the credentials do not match.
        """
        role, stored = _ACCOUNTS.get(username, _UNKNOWN)
        matches = bcrypt.checkpw(password.encode("utf-8"), stored.encode("ascii"))
        return Principal(username=username, role=role) if matches and role else None
