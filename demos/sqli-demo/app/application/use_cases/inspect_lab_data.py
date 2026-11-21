from ...domain.models import LabSnapshot
from ...domain.ports import LabDataInspector


class InspectLabDataUseCase:
    """Reads the lab data for the debug endpoint.

    Args:
        inspector: Reads the database contents.
    """

    def __init__(self, inspector: LabDataInspector) -> None:
        self._inspector = inspector

    def execute(self) -> LabSnapshot:
        """Returns the stored users and secrets."""
        return self._inspector.snapshot()
