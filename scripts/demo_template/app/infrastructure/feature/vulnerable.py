"""Vulnerable variant of the feature, deliberately. For the lab only."""
from ...domain.models import FeatureResult, Principal
# [postgres]
from ..database import PostgresDatabase
# [/postgres]


class VulnerableFeature:
    """The feature, implemented with the vulnerability the demo teaches.
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
        """Runs the feature the vulnerable way.

        Args:
            value: The input the user submitted.
            principal: The authenticated user.

        Returns:
            The feature's result.
        """
        # TODO(attack): implement the feature with the vulnerability this demo teaches.
        return FeatureResult(result=f"received: {value}")
