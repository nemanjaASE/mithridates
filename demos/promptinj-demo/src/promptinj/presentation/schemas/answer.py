from pydantic import BaseModel

from ...domain.entities import AssistantAnswer, Variant


class AssistantTraceOut(BaseModel):
    """How the answer was produced.

    The prompt and the unfiltered output are returned only for `vulnerable`. For `mitigated`
    the trace contains counts, owners and settings, never document text.
    """

    # Full instructor trace — vulnerable route only.
    prompt_sent: str | None = None  # lab switch EXPOSE_PROMPT_TRACE
    raw_answer: str | None = None  # lab switch EXPOSE_RAW_OUTPUT (bypasses the output check)
    # Safe diagnostics — emitted on both routes.
    block_reason: str | None = None
    retrieved_documents: int | None = None
    retrieval_scope: str | None = None  # "owner" | "all owners"
    context_fields: str | None = None  # "allow-listed" | "every field"
    context_owners: list[str] | None = None
    prompt_chars: int | None = None


class AnswerOut(BaseModel):
    # The real response a production system would actually return:
    """Response of the assistant endpoint."""

    mode: str
    answer: str
    blocked: bool
    # Everything educational/diagnostic is grouped here (omitted when empty):
    trace: AssistantTraceOut | None = None

    @classmethod
    def from_result(cls, result: AssistantAnswer, expose_prompt: bool, expose_raw: bool) -> AnswerOut:
        """Builds the response from an assistant answer.

        Args:
            result: The answer.
            expose_prompt: Whether the prompt is included.
            expose_raw: Whether the unfiltered output is included.

        Returns:
            The response model.
        """
        facts = result.retrieval
        prompt_text = result.prompt.user if result.prompt else ""
        # The mitigated route never returns content that bypasses its own protections,
        # whatever the lab switches say.
        unsafe_allowed = result.variant is Variant.VULNERABLE
        trace = AssistantTraceOut(
            prompt_sent=prompt_text if (expose_prompt and unsafe_allowed) else None,
            raw_answer=result.raw_output if (expose_raw and unsafe_allowed) else None,
            block_reason=result.block_reason,
            retrieved_documents=facts.documents if facts else None,
            retrieval_scope=("owner" if facts.scoped_to_owner else "all owners") if facts else None,
            context_fields=("allow-listed" if facts.safe_fields else "every field") if facts else None,
            context_owners=list(facts.owners) if facts else None,
            prompt_chars=len(prompt_text),
        )
        return cls(
            mode=result.variant.value,
            answer=result.answer,
            blocked=result.blocked,
            trace=trace,
        )
