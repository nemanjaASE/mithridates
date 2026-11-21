"""Runs the Alembic migrations from the seed job, on its own connection."""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from .session import Database

_logger = logging.getLogger("promptinj.db")
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _config() -> Config:
    """Builds the Alembic configuration in memory."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    return config


def upgrade_to_head(admin: Database) -> None:
    """Brings the schema to the latest version.

    Args:
        admin: The admin connection pool.
    """
    config = _config()
    # One transaction: the whole upgrade applies, or none of it does.
    with admin.engine.begin() as connection:
        # The `vector` extension is created by the first revision, so this works on a
        # bare database and `uv run alembic upgrade head` behaves identically.
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    _logger.info("Schema is at head.")

