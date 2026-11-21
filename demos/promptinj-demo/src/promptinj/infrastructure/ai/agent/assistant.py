"""Adapts a compiled agent to the `Assistant` port."""
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from ....domain.entities import AssistantAnswer, ToolInvocation, ToolOutcome
from ..common.messages import text_of
from ..common.prompts import PromptSet
from .context import AgentContext
from .spec import ToolAgentSpec

NO_ANSWER = "The assistant did not produce an answer."


def _outcome(result: ToolMessage | None) -> ToolOutcome:
    """Classifies a tool call from the message it produced.

    Args:
        result: The tool's message, or None if there is none.

    Returns:
        The outcome of the call.
    """
    if result is None or getattr(result, "status", "success") == "error":
        return ToolOutcome.NOT_EXECUTED
    artifact = result.artifact or {}
    if artifact.get("executed", True) is False:
        return ToolOutcome.NOT_EXECUTED
    return ToolOutcome.AUTHORIZED if artifact.get("allowed", True) else ToolOutcome.DENIED


def _invocations(messages: list[BaseMessage]) -> tuple[ToolInvocation, ...]:
    """Pairs every tool call the model requested with its outcome.

    Args:
        messages: The run's message history.

    Returns:
        The tool calls, in order.
    """
    results = {m.tool_call_id: m for m in messages if isinstance(m, ToolMessage)}
    return tuple(
        ToolInvocation(call["name"], dict(call.get("args") or {}), _outcome(results.get(call["id"])))
        for message in messages
        if isinstance(message, AIMessage)
        for call in (message.tool_calls or [])
    )


def _last_answer(messages: list[BaseMessage]) -> str:
    """Returns the last text the model produced, ignoring tool messages.

    Args:
        messages: The run's message history.

    Returns:
        The answer.
    """
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            text = text_of(message.content)
            if text.strip():
                return text
    return NO_ANSWER


class ToolAgentAssistant:
    """Runs a compiled agent for one question.

    Args:
        spec: The agent's specification.
        prompts: The agent's prompt templates.
        agent: The compiled agent.
    """

    def __init__(self, spec: ToolAgentSpec, prompts: PromptSet, agent) -> None:
        self._spec = spec
        self._prompts = prompts
        self._agent = agent
        self._base = spec.render_values()

    def answer(self, question: str, current_user_id: str) -> AssistantAnswer:
        """Answers a question, letting the model call its tools.

        Args:
            question: The user's question.
            current_user_id: The user id from the verified token.

        Returns:
            The answer and the tool calls the model made.
        """
        system = self._prompts.render(
            self._spec.system_prompt, **self._base, current_user_id=current_user_id
        )
        state = self._agent.invoke(
            {"messages": [SystemMessage(content=system), HumanMessage(content=question)]},
            context=AgentContext(current_user_id=current_user_id),
        )
        messages = state["messages"]
        answer = _last_answer(messages)
        return AssistantAnswer(
            variant=self._spec.variant,
            answer=answer,
            raw_output=answer,
            tool_invocations=_invocations(messages),
        )
