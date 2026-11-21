"""Builds a RAG assistant from a spec.

    retrieve -> prompt -> generate -> guard -> END

The graph is compiled once at startup. An undeclared template, an unsupplied placeholder
or an unknown output filter stops the process at build time.
"""
from langgraph.graph import END, START, StateGraph

from ....application.errors import ConfigurationError
from ....application.ports import Assistant
from ..common.prompts import PromptSet
from .assistant import RagAssistant
from .deps import RagDeps
from .nodes.build_prompt import make_build_prompt
from .nodes.generate import make_generate
from .nodes.guard_output import make_guard_output
from .nodes.retrieve import make_retrieve
from .spec import RagSpec
from .state import RagState

# Placeholders the nodes supply at render time, besides the spec's own.
RENDER_VALUES = ("current_user_id", "question", "context")


def _prompts(spec: RagSpec, deps: RagDeps) -> PromptSet:
    """Loads the spec's templates and checks their placeholders."""
    required = (spec.system_prompt, spec.user_prompt)
    missing = tuple(name for name in required if name not in spec.prompt_files)
    if missing:
        raise ConfigurationError(
            f"Assistant {spec.name!r} needs the prompt file(s) {', '.join(missing)}, but "
            f"its spec declares {spec.prompt_files or '()'}."
        )
    loaded = deps.prompts.load(spec.name, spec.prompt_files)
    loaded.validate(set(RENDER_VALUES) | set(spec.render_values()))
    return loaded


def build_rag_assistant(spec: RagSpec, deps: RagDeps) -> Assistant:
    """Builds a RAG assistant.

    Args:
        spec: The assistant's specification.
        deps: The retriever, model provider, prompts and output filters.

    Returns:
        The assistant.

    Raises:
        ConfigurationError: The spec is invalid.
    """
    prompts = _prompts(spec, deps)
    graph = StateGraph(RagState)
    graph.add_node("retrieve", make_retrieve(spec, deps))
    graph.add_node("prompt", make_build_prompt(spec, prompts, deps))
    graph.add_node("generate", make_generate(spec, deps))
    graph.add_node("guard", make_guard_output(spec, deps))
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "prompt")
    graph.add_edge("prompt", "generate")
    graph.add_edge("generate", "guard")
    graph.add_edge("guard", END)
    return RagAssistant(spec, graph.compile())
