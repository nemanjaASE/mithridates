"""Creates the `lab_app` role and grants it read-only access. Runs once, as admin.

`lab_app` gets SELECT on three tables, read-only transactions and a statement timeout.
The role name and password are escaped, since DDL accepts no bind parameters.
"""
import logging

from sqlalchemy import String, text

from ..settings import DatabaseCredentials
from .session import Database

_logger = logging.getLogger("promptinj.db")
_STATEMENT_TIMEOUT = "5s"
_READABLE_TABLES = ("accounts", "credentials", "documents")


def grant_least_privilege(admin: Database, app: DatabaseCredentials) -> None:
    """Creates or updates the application role and grants it SELECT on the lab tables.

    Args:
        admin: The admin connection pool.
        app: The application account.
    """
    dialect = admin.engine.dialect
    quote_name = dialect.identifier_preparer.quote
    quote_literal = String().literal_processor(dialect=dialect)

    role = quote_name(app.user)
    with admin.engine.begin() as conn:
        database = quote_name(conn.engine.url.database or "")
        exists = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :name"), {"name": app.user}
        ).fetchone()
        if not exists:
            conn.execute(text(f"CREATE ROLE {role} LOGIN"))
        conn.execute(
            text(
                f"ALTER ROLE {role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE "
                f"PASSWORD {quote_literal(app.password)}"
            )
        )
        conn.execute(text(f"ALTER ROLE {role} SET default_transaction_read_only = on"))
        conn.execute(
            text(f"ALTER ROLE {role} SET statement_timeout = {quote_literal(_STATEMENT_TIMEOUT)}")
        )
        for statement in (
            f"REVOKE ALL ON DATABASE {database} FROM PUBLIC",
            "REVOKE ALL ON SCHEMA public FROM PUBLIC",
            f"GRANT CONNECT ON DATABASE {database} TO {role}",
            f"GRANT USAGE ON SCHEMA public TO {role}",
            f"GRANT SELECT ON {', '.join(_READABLE_TABLES)} TO {role}",
        ):
            conn.execute(text(statement))
    _logger.info("Role %s granted SELECT on %s.", app.user, ", ".join(_READABLE_TABLES))
