"""SQLAlchemy and Alembic backend over PostgreSQL.

    session.py       the engine and the two kinds of transaction
    models.py        the ORM models, the source of the migrations
    migrations/      Alembic environment and revisions
    migrate.py       runs the migrations for the seed job
    privileges.py    the `lab_app` role and its grants
    seeding.py       writes the lab data
    vector.py        pgvector value encoding
    provisioning.py  the `Provisioner` implementation
    repositories/    one repository per table
"""
