"""Entry point of the seed job: `python -m promptinj.seed`. Runs as admin.

1. Brings the schema to the latest version.
2. Creates the `lab_app` role and its privileges.
3. Writes the accounts and credentials.
4. Embeds and writes the documents.

Each step is one transaction; the job can be re-run, since every write replaces.
"""
import logging

from .config import SeedSettings
from .infrastructure.db.factory import PersistenceFactory
from .infrastructure.embeddings.factory import EmbedderFactory
from .infrastructure.ingestion.corpus import SEED_DOCUMENTS
from .infrastructure.ingestion.seed_accounts import SEED_ACCOUNTS, SEED_PASSWORD_HASHES


def main() -> None:
    """Reads the seed settings and runs the four steps."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log = logging.getLogger("promptinj.seed")
    settings = SeedSettings.from_env()
    # Whichever backend `DB_BACKEND` names; this file never learns which one it got.
    db = PersistenceFactory(settings.persistence).provisioner(settings.server, settings.admin)

    db.migrate()
    # After the tables exist, so SELECT can be granted on them.
    db.grant_least_privilege(settings.app_db)
    db.write_accounts(SEED_ACCOUNTS, SEED_PASSWORD_HASHES)

    embedder = EmbedderFactory(settings.embeddings).build()
    # Embed the full text so ranking is identical for both variants; the allow-listed
    # projection is stored next to it and chosen at query time.
    vectors = embedder.embed([text for _, text, _ in SEED_DOCUMENTS])
    embedded = [
        (owner, text, safe, vector)
        for (owner, text, safe), vector in zip(SEED_DOCUMENTS, vectors, strict=True)
    ]
    db.write_documents(embedded)
    log.info("Lab data ready (embedding model=%s).", settings.embeddings.model)


if __name__ == "__main__":
    main()
