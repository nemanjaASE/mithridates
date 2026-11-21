from pydantic import BaseModel

from ...domain.entities import AssistantAnswer


class ToolCallOut(BaseModel):
    """A tool call in the agent's trace: tool, arguments and outcome."""

    account_id: str
    # True only when the tool ran AND the policy allowed it. Unchanged field, unchanged
    # meaning — existing consumers keep working.
    authorized: bool
    # Distinguishes a refusal by the tool from a call that never ran: no budget left, an
    # unknown tool name, or arguments that did not match the schema.
    outcome: str


class AgentTraceOut(BaseModel):
    """The tool calls the model made and their outcomes. Returned only when enabled."""

    tool_calls: list[ToolCallOut] | None = None  # lab switch EXPOSE_PROMPT_TRACE


class AgentAnswerOut(BaseModel):
    # The real response a production system would actually return:
    """Response of the agent endpoint."""

    mode: str
    answer: str
    # Everything educational/diagnostic is grouped here (omitted when empty):
    trace: AgentTraceOut | None = None

    @classmethod
    def from_result(cls, result: AssistantAnswer, expose_trace: bool) -> "AgentAnswerOut":
        """Builds the response from an assistant answer.

        Args:
            result: The answer.
            expose_trace: Whether the tool calls are included.

        Returns:
            The response model.
        """
        trace = (
            AgentTraceOut(
                tool_calls=[
                    ToolCallOut(
                        # Mapped here, at the boundary: the agent runtime records the
                        # arguments the model sent, and this demo's API happens to show
                        # one of them. The runtime is not tied to that choice.
                        account_id=str(i.arguments.get("account_id", "")),
                        authorized=i.authorized,
                        outcome=i.outcome.value,
                    )
                    for i in result.tool_invocations
                ]
            )
            if expose_trace
            else None
        )
        return cls(mode=result.variant.value, answer=result.answer, trace=trace)
