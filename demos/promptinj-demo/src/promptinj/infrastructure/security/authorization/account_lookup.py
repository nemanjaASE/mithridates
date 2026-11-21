"""The two authorization policies of the `get_account` tool."""
from ....application.ports import AccountRepository
from ....domain.entities import Account, AccountLookupResult


def render_account(account: Account, *, mask_card: bool) -> str:
    """Renders an account as tool output.

    Args:
        account: The account.
        mask_card: Shows only the last four digits of the card number.

    Returns:
        The text the model receives.
    """
    card = f"****{account.card_last4}" if mask_card else account.card_number
    return (
        f"id={account.id} | name={account.name} | email={account.email} "
        f"| plan={account.plan} | balance={account.balance_rsd} RSD | card={card}"
    )


class UnrestrictedAccountLookup:
    """Returns any existing account without an ownership check (deliberately vulnerable).

    Args:
        repository: Reads account records.
    """

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def lookup(self, account_id: str) -> AccountLookupResult:
        """Returns the requested account.

        Args:
            account_id: The id the model asked for.

        Returns:
            The account, or a not-found result.
        """
        account = self._repository.get(account_id)
        if account is None:
            return AccountLookupResult(False, f"Account {account_id} does not exist.")
        return AccountLookupResult(True, render_account(account, mask_card=True))


class OwnerScopedAccountLookup:
    """Returns only the authenticated user's own account.

    Args:
        repository: Reads account records.
        current_user_id: The user id from the verified token.
    """

    def __init__(self, repository: AccountRepository, current_user_id: str) -> None:
        self._repository = repository
        self._current_user_id = current_user_id

    def lookup(self, account_id: str) -> AccountLookupResult:
        """Returns the requested account if it belongs to the authenticated user.

        Args:
            account_id: The id the model asked for.

        Returns:
            The account, or a refusal.
        """
        if account_id != self._current_user_id:
            return AccountLookupResult(False, f"DENIED: you are not authorized to access account {account_id}.")
        account = self._repository.get(account_id)
        if account is None:
            return AccountLookupResult(False, f"Account {account_id} does not exist.")
        return AccountLookupResult(True, render_account(account, mask_card=True))
