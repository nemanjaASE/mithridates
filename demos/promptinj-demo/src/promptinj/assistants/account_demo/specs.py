"""The four assistants, as data.

RAG pair, `assistant-vulnerable` and `assistant-mitigated`, which differ in:

1. `scope_to_owner`: the search covers only the user's own documents.
2. `safe_fields`: only allow-listed fields are read; the full card number is not.
3. `output_filters`: the answer is checked before it is returned.
4. `delimiters` and their prompts: the question is marked as data.

Agent pair, `agent-vulnerable` and `agent-mitigated`: identical specs, except for the
authorization policy in `TOOL_POLICIES`.
"""
from pathlib import Path

from ...domain.entities import Variant
from ...infrastructure.ai.agent import ToolAgentSpec
from ...infrastructure.ai.rag import Delimiters, RagSpec, RetrievalConfig
from .tools import GET_ACCOUNT, ToolPolicy

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

ASSISTANT_VULNERABLE = RagSpec(
    name="assistant-vulnerable",
    description="RAG assistant, unscoped retrieval, full documents, no output filter",
    variant=Variant.VULNERABLE,
    retrieval=RetrievalConfig(
        scope_to_owner=False,  # unscoped: other users' documents can surface
        safe_fields=False,  # and every field of them, full PAN included
    ),
    output_filters=(),
)

ASSISTANT_MITIGATED = RagSpec(
    name="assistant-mitigated",
    description="RAG assistant, owner-scoped retrieval, allow-listed fields, PAN filter",
    variant=Variant.MITIGATED,
    retrieval=RetrievalConfig(
        scope_to_owner=True,  # least privilege: only the JWT user's documents
        safe_fields=True,  # and only the allow-listed fields of them
    ),
    output_filters=("card_number",),
    delimiters=Delimiters(),
)

AGENT_VULNERABLE = ToolAgentSpec(
    name="agent-vulnerable",
    description="tool agent, account lookup with no ownership check (IDOR)",
    variant=Variant.VULNERABLE,
    tools=(GET_ACCOUNT,),
)

AGENT_MITIGATED = ToolAgentSpec(
    name="agent-mitigated",
    description="tool agent, account lookup bound to the logged-in user",
    variant=Variant.MITIGATED,
    tools=(GET_ACCOUNT,),
)

RAG_SPECS: tuple[RagSpec, ...] = (ASSISTANT_VULNERABLE, ASSISTANT_MITIGATED)
AGENT_SPECS: tuple[ToolAgentSpec, ...] = (AGENT_VULNERABLE, AGENT_MITIGATED)

# The authorization policy of each agent. Kept out of the spec: the tool is built already
# bound to its policy, so the agent runtime never chooses one.
TOOL_POLICIES: dict[str, ToolPolicy] = {
    AGENT_VULNERABLE.name: ToolPolicy.UNRESTRICTED,
    AGENT_MITIGATED.name: ToolPolicy.OWNER_SCOPED,
}
