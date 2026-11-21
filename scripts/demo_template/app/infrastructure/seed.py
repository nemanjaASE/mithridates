"""Creates the application account, the schema and the data. Runs once, as admin.

`lab_app` gets SELECT on the lab tables, read-only transactions and a statement timeout.
"""
import psycopg
from psycopg import sql

from .database import DatabaseCredentials, PostgresDatabase

# TODO(attack): replace the sample table with the data your attack needs.
_SCHEMA = """
DROP TABLE IF EXISTS items;
CREATE TABLE items (
    id    serial PRIMARY KEY,
    owner TEXT NOT NULL,
    name  TEXT NOT NULL
);
"""
SEED_ITEMS = (
    ("ana", "notebook"),
    ("admin", "server key"),
)
_TABLES = ("items",)
_STATEMENT_TIMEOUT = "5s"


def reset_database(admin: PostgresDatabase, app: DatabaseCredentials) -> None:
    """Drops and recreates the schema, the application account and the data.

    Args:
        admin: Connections for the admin account.
        app: The application account to create.
    """
    with admin.connect() as conn, conn.transaction():
        _ensure_login_role(conn, app)
        conn.execute(_SCHEMA)
        conn.cursor().executemany("INSERT INTO items (owner, name) VALUES (%s, %s)", SEED_ITEMS)
        _grant_read_only(conn, sql.Identifier(app.user))


def _ensure_login_role(conn: psycopg.Connection, credentials: DatabaseCredentials) -> None:
    """Creates the login role, or updates its password if it exists."""
    role = sql.Identifier(credentials.user)
    exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (credentials.user,)).fetchone()
    if not exists:
        conn.execute(sql.SQL("CREATE ROLE {} LOGIN").format(role))
    conn.execute(
        sql.SQL("ALTER ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}").format(
            role, sql.Literal(credentials.password)
        )
    )
    conn.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(role))
    conn.execute(
        sql.SQL("ALTER ROLE {} SET statement_timeout = {}").format(role, sql.Literal(_STATEMENT_TIMEOUT))
    )


def _grant_read_only(conn: psycopg.Connection, app: sql.Identifier) -> None:
    """Grants the application account SELECT on the lab tables and nothing more."""
    database = sql.Identifier(conn.info.dbname)
    tables = sql.SQL(", ").join(sql.Identifier(t) for t in _TABLES)
    statements = (
        sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(database),
        sql.SQL("REVOKE ALL ON SCHEMA public FROM PUBLIC"),
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(database, app),
        sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(app),
        sql.SQL("GRANT SELECT ON {} TO {}").format(tables, app),
    )
    for statement in statements:
        conn.execute(statement)
