"""The account assistants: four specs, one tool and their prompts.

    specs.py     the four assistants and the tool policy of each agent
    tools.py     `get_account` and its authorization policy
    schemas.py   the argument schema the model sees
    prompts/     `_default/` and one directory per assistant that overrides it
"""
from .specs import (
    AGENT_MITIGATED,
    AGENT_SPECS,
    AGENT_VULNERABLE,
    ASSISTANT_MITIGATED,
    ASSISTANT_VULNERABLE,
    PROMPTS_DIR,
    RAG_SPECS,
    TOOL_POLICIES,
)
from .tools import GET_ACCOUNT, ToolPolicy, account_tools

__all__ = [
    "AGENT_MITIGATED",
    "AGENT_SPECS",
    "AGENT_VULNERABLE",
    "ASSISTANT_MITIGATED",
    "ASSISTANT_VULNERABLE",
    "GET_ACCOUNT",
    "PROMPTS_DIR",
    "RAG_SPECS",
    "TOOL_POLICIES",
    "ToolPolicy",
    "account_tools",
]
