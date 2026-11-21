"""Builds a tool-using agent from a spec with `langchain.agents.create_agent`.

The library provides the loop, routing, argument validation and the step limit
(`ModelCallLimitMiddleware`). This module adds `ToolCallBudget` and checks the spec.
"""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware

from ....application.errors import ConfigurationError
from ....application.ports import Assistant
from .assistant import ToolAgentAssistant
from .budget import ToolCallBudget
from .context import AgentContext
from .deps import AgentDeps
from .spec import ToolAgentSpec

# The placeholder the system prompt may use, besides whatever the spec supplies.
RENDER_VALUES = ("current_user_id",)


def _check(spec: ToolAgentSpec, deps: AgentDeps) -> None:
    """Rejects a spec whose tools, prompts or limits do not match its dependencies."""
    if not spec.tools:
        raise ConfigurationError(
            f"Assistant {spec.name!r} is a tool agent with no tools."
        )
    missing = tuple(name for name in spec.tools if name not in deps.tools.names)
    if missing:
        raise ConfigurationError(
            f"Assistant {spec.name!r} declares tool(s) {', '.join(missing)}, which are "
            f"not registered. Available: {', '.join(deps.tools.names) or 'none'}."
        )
    if spec.system_prompt not in spec.prompt_files:
        raise ConfigurationError(
            f"Assistant {spec.name!r} needs the prompt file {spec.system_prompt!r}, but "
            f"its spec declares {spec.prompt_files or '()'}."
        )
    for label, value in (
        ("max_tool_calls", spec.max_tool_calls),
        ("max_model_steps", spec.max_model_steps),
    ):
        if value < 1:
            raise ConfigurationError(
                f"Assistant {spec.name!r} sets {label}={value}; it must be at least 1."
            )


def build_tool_agent(spec: ToolAgentSpec, deps: AgentDeps) -> Assistant:
    """Builds an agent assistant.

    Args:
        spec: The agent's specification.
        deps: The model provider, tools and prompts.

    Returns:
        The assistant.

    Raises:
        ConfigurationError: The spec is invalid.
    """
    _check(spec, deps)
    prompts = deps.prompts.load(spec.name, spec.prompt_files)
    prompts.validate(set(RENDER_VALUES) | set(spec.render_values()))

    agent = create_agent(
        model=deps.llm.for_role(spec.model_role),
        tools=deps.tools.langchain_tools(spec.tools),
        # The identity is NOT in the prompt or the tool arguments; it rides the context.
        context_schema=AgentContext,
        middleware=[
            ToolCallBudget(spec.max_tool_calls),
            ModelCallLimitMiddleware(
                run_limit=spec.max_model_steps, exit_behavior="end"
            ),
        ],
    )
    return ToolAgentAssistant(spec, prompts, agent)
