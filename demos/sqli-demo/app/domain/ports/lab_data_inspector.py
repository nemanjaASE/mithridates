from typing import Protocol

from ..models import LabSnapshot


class LabDataInspector(Protocol):
    """Reads the lab data for the debug endpoint."""

    def snapshot(self) -> LabSnapshot:
        """Returns the stored users and secrets."""
