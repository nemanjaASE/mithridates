"""Entry point of the seed job: `python -m app.seed`."""
import logging

from .config import SeedSettings
from .infrastructure.database import PostgresDatabase
from .infrastructure.seed import reset_database


def main() -> None:
    """Reads the seed settings and resets the database."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = SeedSettings.from_env()
    reset_database(PostgresDatabase(settings.server, settings.admin), app=settings.app_db)
    logging.getLogger("app.seed").info("Database reset and seeded.")


if __name__ == "__main__":
    main()
