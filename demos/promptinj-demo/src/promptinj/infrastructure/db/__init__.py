"""Persistence.

    settings.py       connection settings, without a driver import
    provisioning.py   what a backend does at startup: migrate, grant, seed
    factory.py        selects the backend named by DB_BACKEND
    sqlalchemy/       the SQLAlchemy and Alembic backend over PostgreSQL
"""
