"""Specification of a retrieval-augmented assistant."""
from dataclasses import dataclass, field

from ....domain.entities import Variant


@dataclass(frozen=True)
class Delimiters:
    """The markers that enclose the untrusted question."""

    start: str = "[DATA_START]"
    end: str = "[DATA_END]"


@dataclass(frozen=True)
class RetrievalConfig:
    """Retrieval settings.

    `scope_to_owner` decides whose documents are searched; `safe_fields` decides which
    fields are returned; `top_k` how many documents.
    """

    scope_to_owner: bool
    safe_fields: bool
    top_k: int = 4


@dataclass(frozen=True)
class RagSpec:
    """A RAG assistant: model role, prompt templates, retrieval and output filters."""

    name: str
    description: str
    variant: Variant
    retrieval: RetrievalConfig
    model_role: str = "cheap"  # one completion, no tool calling
    prompt_files: tuple[str, ...] = ("system", "user")
    system_prompt: str = "system"
    user_prompt: str = "user"
    # Names resolved against `RagDeps.output_filters`; empty means the output is returned
    # as is.
    output_filters: tuple[str, ...] = ()
    # Present only when the prompts delimit untrusted input (spotlighting).
    delimiters: Delimiters | None = None
    prompt_values: dict[str, str] = field(default_factory=dict)

    def render_values(self) -> dict[str, str]:
        """Returns the template values that come from the spec.

        Returns:
            The values, by placeholder name.
        """
        values = dict(self.prompt_values)
        if self.delimiters is not None:
            values["data_start"] = self.delimiters.start
            values["data_end"] = self.delimiters.end
        return values
