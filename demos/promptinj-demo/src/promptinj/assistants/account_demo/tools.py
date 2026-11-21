"""The `get_account` tool and the authorization policy of each agent.

The policy is bound when the tool is built. The caller's identity comes from the verified
token, never from the arguments the model writes. Every lookup is audited.
"""
from collections.abc import Callable
from enum import Enum

from ...application.errors import ConfigurationError
from ...application.ports import AccountLookupTool, AccountRepository, AuditLog
from ...infrastructure.ai.agent import ToolDefinition, ToolRegistry, ToolRequest, ToolResult
from ...infrastructure.security.authorization.account_lookup import (
    OwnerScopedAccountLookup,
    UnrestrictedAccountLookup,
)
from .schemas import GetAccountArgs

GET_ACCOUNT = "get_account"


class ToolPolicy(str, Enum):
    """How `get_account` authorizes a lookup.

    UNRESTRICTED  serves any existing account (the deliberate vulnerability).
    OWNER_SCOPED  serves only the authenticated user's own account.
    """

    UNRESTRICTED = "unrestricted"
    OWNER_SCOPED = "owner-scoped"


_POLICIES: dict[ToolPolicy, Callable[[AccountRepository, str], AccountLookupTool]] = {
    ToolPolicy.OWNER_SCOPED: OwnerScopedAccountLookup,
    ToolPolicy.UNRESTRICTED: lambda accounts, _user_id: UnrestrictedAccountLookup(accounts),
}


def get_account_tool(
    accounts: AccountRepository, policy: ToolPolicy, audit: AuditLog
) -> ToolDefinition:
    """Builds `get_account` bound to one authorization policy.

    Args:
        accounts: Reads account records.
        policy: The authorization policy.
        audit: Records each lookup.

    Returns:
        The tool definition.
    """
    try:
        bind = _POLICIES[policy]
    except KeyError:
        raise ConfigurationError(
            f"Tool policy {policy!r} grants no access and cannot run a lookup. "
            f"Supported: {', '.join(sorted(p.value for p in _POLICIES))}."
        ) from None

    def execute(args: GetAccountArgs, request: ToolRequest) -> ToolResult:
        # The id to serve is decided by the policy from the TRUSTED user id; the model's
        # `account_id` is only what it asked for.
        """Looks up the requested account if the policy allows it.

        Args:
            args: The arguments the model supplied.
            request: The authenticated user's context.

        Returns:
            The account, or a refusal.
        """
        result = bind(accounts, request.current_user_id).lookup(args.account_id)
        audit.tool_call(
            GET_ACCOUNT,
            {"account_id": args.account_id},
            "authorized" if result.authorized else "denied",
        )
        return ToolResult(content=result.content, allowed=result.authorized)

    return ToolDefinition(
        name=GET_ACCOUNT,
        description="Look up a single customer account by its id (e.g. u-1001).",
        args_schema=GetAccountArgs,
        execute=execute,
    )


def account_tools(
    accounts: AccountRepository, policy: ToolPolicy, audit: AuditLog
) -> ToolRegistry:
    """Builds the tool registry of one agent.

    Args:
        accounts: Reads account records.
        policy: The authorization policy.
        audit: Records each lookup.

    Returns:
        The registry.
    """
    return ToolRegistry([get_account_tool(accounts, policy, audit)])
