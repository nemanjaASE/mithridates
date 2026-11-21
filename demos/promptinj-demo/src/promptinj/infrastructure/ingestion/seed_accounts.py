"""The seed accounts. Fixed values, so the attacks are reproducible."""
from ...domain.entities import Account

SEED_ACCOUNTS = (
    Account("u-1001", "Ana Jovanović", "ana.jovanovic@akme.rs", "Premium", 84250, "4921 7654 3210 4421"),
    Account("u-1002", "Marko Petrović", "marko.petrovic@akme.rs", "Standard", 12300, "5188 2290 7761 8830"),
    Account("u-1003", "Jelena Kovač", "jelena.kovac@akme.rs", "Premium", 256900, "4000 1234 5678 9010"),
)

CURRENT_USER_ID = "u-1001"

# Login passwords are stored ONLY as bcrypt hashes (plaintext for the lab, in comments,
# so students can log in). Hashing was done server-side; the app only verifies.
#   ana.jovanovic@akme.rs   -> Ana#2024!
#   marko.petrovic@akme.rs  -> Marko#2024!
#   jelena.kovac@akme.rs    -> Jelena#2024!
SEED_PASSWORD_HASHES = {
    "ana.jovanovic@akme.rs": "$2b$10$3wvsRlJoOgpP1R9NuOOHtuiUARK7C2ASO1LLdtUo1KvioG.cR80X.",
    "marko.petrovic@akme.rs": "$2b$10$Y9hLltMKg03cGO/wP8AayuDEvaL06WsJy9nR5mMZZ39x1wBgUd/8.",
    "jelena.kovac@akme.rs": "$2b$10$9wOeD2S2hrmXBV/7MDg63OO5j5jfQ6Nd.W5FnccQI1Tp1AtWgOnHW",
}
