"""Limits the tool calls per run that actually reach a tool.

Unlike `ToolCallLimitMiddleware`, which counts the calls the model requests, calls with
an unknown tool name or invalid arguments are not counted. Several calls in one model
message are evaluated against the same state, so earlier calls in the batch are counted
too. Nothing is stored on the instance.
"""
from collections.abc import Callable

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import AIMessage, ToolMessage
from pydantic import ValidationError

#: Marks a `ToolMessage` this middleware produced instead of running the tool.
NOT_EXECUTED = {"executed": False}


def _reaches_a_tool(tool, args: dict) -> bool:
    """Whether a call will reach a tool: the name resolves and the arguments validate.

    Args:
        tool: The resolved tool, or None.
        args: The arguments the model supplied.

    Returns:
        Whether the call will be executed.
    """
    if tool is None:
        return False
    schema = getattr(tool, "args_schema", None)
    if schema is None:
        return True
    try:
        schema.model_validate(dict(args or {}))
    except ValidationError:
        return False
    return True


class ToolCallBudget(AgentMiddleware):
    """Allows at most `limit` executed tool calls per run.

    Args:
        limit: The maximum number of executed tool calls.
    """

    def __init__(self, limit: int) -> None:
        super().__init__()
        self._limit = limit

    @property
    def name(self) -> str:
        """The middleware's name."""
        return f"ToolCallBudget({self._limit})"

    @staticmethod
    def _already_executed(messages: list) -> int:
        """Counts the completed calls that reached a tool."""
        return sum(
            1
            for m in messages
            if isinstance(m, ToolMessage)
            and getattr(m, "status", "success") != "error"
            and (m.artifact or {}).get("executed", True)
        )

    def _earlier_in_batch(self, messages: list, tool_call_id: str, tool) -> int:
        """Counts the calls before this one, in the same message, that will run."""
        last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
        if last_ai is None:
            return 0
        count = 0
        for call in last_ai.tool_calls or []:
            if call["id"] == tool_call_id:
                break
            # Siblings resolve against the same tool set; `tool` stands in for a
            # registered name, which is all `_reaches_a_tool` needs besides the schema.
            sibling = tool if call["name"] == getattr(tool, "name", None) else None
            if _reaches_a_tool(sibling, call.get("args") or {}):
                count += 1
        return count

    def wrap_tool_call(
        self, request: ToolCallRequest, handler: Callable[[ToolCallRequest], object]
    ) -> object:
        """Runs the call if the budget allows it, or refuses it without running.

        Args:
            request: The tool call.
            handler: Executes the call.

        Returns:
            The tool's result, or a refusal.
        """
        state = request.state or {}
        messages = list(state.get("messages") or [])
        spent = self._already_executed(messages) + self._earlier_in_batch(
            messages, request.tool_call["id"], request.tool
        )
        if spent >= self._limit:
            return ToolMessage(
                content=(
                    f"DENIED: this request has already used its budget of "
                    f"{self._limit} tool calls."
                ),
                tool_call_id=request.tool_call["id"],
                artifact=NOT_EXECUTED,
            )
        return handler(request)
