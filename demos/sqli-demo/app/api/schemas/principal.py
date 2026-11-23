from pydantic import BaseModel

from ...domain.models import Principal

# After a UNION attack the claims may contain anything from the database.
ClaimValue = int | float | str | None


class PrincipalOut(BaseModel):
    """Response of `GET /users/me`: the token's owner."""

    id: str
    username: ClaimValue
    role: ClaimValue

    @classmethod
    def from_domain(cls, principal: Principal) -> PrincipalOut:
        """Builds the response from a principal.

        Args:
            principal: The authenticated user.

        Returns:
            The response model.
        """
        return cls(id=principal.user_id, username=principal.username, role=principal.role)
