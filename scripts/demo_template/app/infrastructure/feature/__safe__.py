"""__Safe__ variant of the feature: the same behaviour, with the defense."""
from ...domain.models import FeatureResult, Principal
# [postgres]
from ..database import PostgresDatabase
# [/postgres]


class __Safe__Feature:
    """The feature, implemented with the defense.
    # [postgres]

    Args:
        db: Connections for the application's database account.
    # [/postgres]
    """
# [postgres]

    def __init__(self, db: PostgresDatabase) -> None:
        self._db = db
# [/postgres]

    def run(self, value: str, principal: Principal) -> FeatureResult:
        """Runs the feature with the defense.

        Args:
            value: The input the user submitted.
            principal: The authenticated user.

        Returns:
            The feature's result.
        """
        # TODO(attack): implement the same feature with the defense.
        return FeatureResult(result=f"received: {value}")
