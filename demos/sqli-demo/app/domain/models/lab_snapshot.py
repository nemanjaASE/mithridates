from dataclasses import dataclass

from .user import User


@dataclass(frozen=True)
class LabSnapshot:
    """The users and secrets stored in the database."""

    users: tuple[User, ...]
    secret_names: tuple[str, ...]
