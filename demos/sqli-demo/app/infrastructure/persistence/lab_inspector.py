"""Reads the lab data as `lab_legacy`, the only account that can read `secrets`."""
from ...domain.models import LabSnapshot, User
from .database import PostgresDatabase


class PostgresLabInspector:
    """Reads the stored users and secrets.

    Args:
        db: Connections for the `lab_legacy` account.
    """

    def __init__(self, db: PostgresDatabase) -> None:
        self._db = db

    def snapshot(self) -> LabSnapshot:
        """Returns the stored users and secrets."""
        with self._db.connect() as conn:
            users = conn.execute("SELECT id, username, role FROM users ORDER BY username").fetchall()
            secrets = conn.execute("SELECT name FROM secrets ORDER BY name").fetchall()
        return LabSnapshot(
            users=tuple(User(id=str(i), username=u, role=r) for i, u, r in users),
            secret_names=tuple(name for (name,) in secrets),
        )
