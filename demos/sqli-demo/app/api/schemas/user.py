from pydantic import BaseModel

from ...domain.models import User

# After a UNION attack the columns may contain any type from the database.
LabValue = int | float | str | None


class UserOut(BaseModel):
    """A user as returned by the debug endpoint."""

    id: LabValue
    username: LabValue
    role: LabValue

    @classmethod
    def from_domain(cls, user: User) -> "UserOut":
        """Builds the response from a user.

        Args:
            user: The domain user.

        Returns:
            The response model.
        """
        return cls(id=user.id, username=user.username, role=user.role)
