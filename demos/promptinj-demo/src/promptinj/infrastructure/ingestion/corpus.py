"""Builds the documents the assistant retrieves, from the seed accounts.

Each document has two renderings, built field by field:

- `text`: every field, including the full card number. Used by the vulnerable variant.
- `safe_text`: only the allow-listed fields below.
"""
from .seed_accounts import SEED_ACCOUNTS

# Fields a document may carry into the mitigated context. Extending a document means
# deciding, here, whether the new field is allowed — the default is that it is not.
PROFILE_FIELDS_ALLOWED = ("name", "email", "plan")
BILLING_FIELDS_ALLOWED = ("balance_rsd", "card_last4")

# How an allowed field is written for the model. The allow-list decides *whether* a field
# may appear; this only decides how it reads.
FIELD_LABELS = {"balance_rsd": "balance", "card_last4": "ending"}


def _profile(account) -> tuple[str, str]:
    """Builds the profile document of an account: full and allow-listed text."""
    body = f"name={account.name}, email={account.email}, plan={account.plan}"
    full = f"Customer profile [{account.id}]: {body}."
    # Nothing on the profile is withheld, but it is still rebuilt from the allow-list
    # so that adding a sensitive field later does not silently reach the model.
    allowed = {"name": account.name, "email": account.email, "plan": account.plan}
    safe_body = ", ".join(f"{f}={allowed[f]}" for f in PROFILE_FIELDS_ALLOWED)
    return full, f"Customer profile [{account.id}]: {safe_body}."


def _billing(account) -> tuple[str, str]:
    """Builds the billing document of an account: full and allow-listed text."""
    full = (
        f"Billing record [{account.id}]: balance={account.balance_rsd} RSD, "
        f"card={account.card_number}, ending={account.card_last4}."
    )
    allowed = {"balance_rsd": f"{account.balance_rsd} RSD", "card_last4": account.card_last4}
    safe_body = ", ".join(
        f"{FIELD_LABELS.get(f, f)}={allowed[f]}" for f in BILLING_FIELDS_ALLOWED
    )
    return full, f"Billing record [{account.id}]: {safe_body}."


def _documents_for(account) -> list[tuple[str, str, str]]:
    """Returns the documents of an account as (owner id, text, safe text)."""
    return [(account.id, *_profile(account)), (account.id, *_billing(account))]


# (owner_id, text, safe_text) triples.
SEED_DOCUMENTS: tuple[tuple[str, str, str], ...] = tuple(
    doc for account in SEED_ACCOUNTS for doc in _documents_for(account)
)
