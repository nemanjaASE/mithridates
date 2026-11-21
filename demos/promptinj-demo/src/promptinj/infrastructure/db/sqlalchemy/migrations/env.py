"""Alembic environment.

Two ways in, and both end up on the same metadata:

- the seed job calls `upgrade_to_head()` in `../migrate.py`, which hands a live
  connection down through `config.attributes`. No URL is read from anywhere, so the
  migration cannot reach a different database than the one being seeded.
- a developer runs `uv run alembic ...` from the project root, and the URL is built from
  the same env variables the seed job uses (`SeedSettings`), because migrations run as
  the admin account — the application's role has no DDL rights at all.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from promptinj.config import SeedSettings
from promptinj.infrastructure.db.sqlalchemy.models import Base
from promptinj.infrastructure.db.sqlalchemy.session import build_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# What `--autogenerate` compares the database against.
target_metadata = Base.metadata


def _render_item(type_, obj, autogen_context) -> bool:
    """Make autogenerate emit the import for pgvector's column type.

    `user_module_prefix` gets the name right (`pgvector.sqlalchemy.VECTOR`) but does not
    add the import, so a generated script would reference a module it never imported.
    Returning False keeps the default rendering.
    """
    if type_ == "type" and type(obj).__module__.startswith("pgvector"):
        autogen_context.imports.add("import pgvector.sqlalchemy")
    return False


def _configure(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        user_module_prefix="pgvector.sqlalchemy.",
        render_item=_render_item,
    )


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (`alembic upgrade head --sql`)."""
    settings = SeedSettings.from_env()
    context.configure(
        url=build_url(settings.server, settings.admin).render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:  # called from the seed job, inside its own transaction
        _configure(connection)
        with context.begin_transaction():
            context.run_migrations()
        return

    settings = SeedSettings.from_env()  # called from the CLI
    engine = create_engine(build_url(settings.server, settings.admin))
    with engine.connect() as conn:
        _configure(conn)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
