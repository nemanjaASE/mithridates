"""Generic tool contract: name, description, argument schema and executor.

The executor is registered already bound to its authorization policy. The caller's
identity arrives in `ToolRequest`, from the trusted context, never from the model.
"""
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from langchain.tools import ToolRuntime
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel

from ....application.errors import ConfigurationError, UnknownTool
from .context import AgentContext


@dataclass(frozen=True)
class ToolRequest:
    """Per-request context of a tool call. Never filled from the model's output."""

    current_user_id: str


@dataclass(frozen=True)
class ToolResult:
    """What a tool returns: the text for the model, and whether the call was allowed."""

    content: str
    allowed: bool = True


ToolExecutor = Callable[[BaseModel, ToolRequest], ToolResult]


@dataclass(frozen=True)
class ToolDefinition:
    """A tool: name, description, argument schema and executor."""

    name: str
    description: str
    args_schema: type[BaseModel]
    execute: ToolExecutor

    def as_langchain_tool(self) -> BaseTool:
        """Wraps the definition as a LangChain tool.

        Returns:
            The tool, which receives the user id from the runtime context.
        """
        schema = self.args_schema
        execute = self.execute

        def run(runtime: ToolRuntime, **kwargs: object) -> tuple[str, dict]:
            """Runs the executor with the validated arguments and the trusted context."""
            context: AgentContext = runtime.context
            result = execute(
                schema.model_validate(kwargs),
                ToolRequest(current_user_id=context.current_user_id),
            )
            return result.content, {"allowed": result.allowed}

        return StructuredTool.from_function(
            func=run,
            name=self.name,
            description=self.description,
            args_schema=schema,
            # Lets the outcome travel as data beside the text the model reads.
            response_format="content_and_artifact",
        )


class ToolRegistry:
    """The tools one assistant may call.

    Args:
        definitions: The tools to register.
    """

    def __init__(self, definitions: Iterable[ToolDefinition] = ()) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: ToolDefinition) -> None:
        """Adds a tool.

        Args:
            definition: The tool to add.

        Raises:
            ConfigurationError: A tool with that name is already registered.
        """
        if definition.name in self._definitions:
            raise ConfigurationError(f"Tool {definition.name!r} is already registered.")
        self._definitions[definition.name] = definition

    @property
    def names(self) -> tuple[str, ...]:
        """Returns the registered tool names."""
        return tuple(sorted(self._definitions))

    def get(self, name: str) -> ToolDefinition:
        """Returns a tool by name.

        Args:
            name: The tool name.

        Returns:
            The tool.

        Raises:
            UnknownTool: No tool has that name.
        """
        try:
            return self._definitions[name]
        except KeyError:
            raise UnknownTool(name) from None

    def langchain_tools(self, names: Iterable[str]) -> list[BaseTool]:
        """Returns the named tools as LangChain tools.

        Args:
            names: The tool names.

        Returns:
            The tools.
        """
        return [self.get(name).as_langchain_tool() for name in names]
