from pydantic import BaseModel

from ...domain.models import LabSnapshot
from .user import UserOut


class LabSnapshotOut(BaseModel):
    """Response of the debug endpoint: the stored users and secrets."""

    users: list[UserOut]
    secret_names: list[str]

    @classmethod
    def from_domain(cls, snapshot: LabSnapshot) -> "LabSnapshotOut":
        """Builds the response from a lab snapshot.

        Args:
            snapshot: The database contents.

        Returns:
            The response model.
        """
        return cls(
            users=[UserOut.from_domain(u) for u in snapshot.users],
            secret_names=list(snapshot.secret_names),
        )
