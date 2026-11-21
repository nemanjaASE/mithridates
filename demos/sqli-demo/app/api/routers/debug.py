from fastapi import APIRouter

from ...application.use_cases import InspectLabDataUseCase
from ..schemas import LabSnapshotOut
from .prefix import API_PREFIX


def build_debug_router(inspect_lab: InspectLabDataUseCase) -> APIRouter:
    """Builds the router for `GET /debug/users`.

    Args:
        inspect_lab: The use case that reads the lab data.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=f"{API_PREFIX}/debug", tags=["debug"])

    @router.get("/users", response_model=LabSnapshotOut)
    def debug_users() -> LabSnapshotOut:
        """Returns the users and secrets stored in the database."""
        return LabSnapshotOut.from_domain(inspect_lab.execute())

    return router
