"""Specification of a tool-using assistant."""
from dataclasses import dataclass, field

from ....domain.entities import Variant

# Defaults, overridable per assistant. See `budget.py` for why there are two numbers:
# one bounds work that reached a tool, the other bounds how often the model is asked.
DEFAULT_MAX_TOOL_CALLS = 3
DEFAULT_MAX_MODEL_STEPS = 5


@dataclass(frozen=True)
class ToolAgentSpec:
    """A tool-using assistant: model role, prompt templates, tools and limits."""

    name: str
    description: str
    variant: Variant
    model_role: str = "strong"  # tool calling is the harder job
    # Template stems loaded from this assistant's prompt directory.
    prompt_files: tuple[str, ...] = ("agent_system",)
    system_prompt: str = "agent_system"
    tools: tuple[str, ...] = ()
    max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS
    max_model_steps: int = DEFAULT_MAX_MODEL_STEPS
    # Extra values merged into every prompt render for this assistant.
    prompt_values: dict[str, str] = field(default_factory=dict)

    def render_values(self) -> dict[str, str]:
        """Returns the values the agent's templates may use.

        Returns:
            The values, by placeholder name.
        """
        return dict(self.prompt_values)
