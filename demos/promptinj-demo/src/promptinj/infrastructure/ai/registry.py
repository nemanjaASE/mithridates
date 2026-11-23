"""Assistants by name. Each is built once, on first use or by `build_all()`."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from ...application.errors import ConfigurationError, UnknownAssistant
from ...application.ports import Assistant

BuildAssistant = Callable[[], Assistant]


@dataclass(frozen=True)
class _Entry:
    """A registered assistant: its description, its build function and the built instance."""

    description: str
    build: BuildAssistant


class AssistantRegistry:
    """Registers assistants by name and builds each one once."""

    def __init__(self) -> None:
        self._entries: dict[str, _Entry] = {}
        self._built: dict[str, Assistant] = {}

    def register(self, name: str, description: str, build: BuildAssistant) -> None:
        """Registers an assistant.

        Args:
            name: The assistant name.
            description: A short description for `GET /`.
            build: Builds the assistant.

        Raises:
            ConfigurationError: The name is already registered.
        """
        if name in self._entries:
            raise ConfigurationError(f"Assistant {name!r} is registered twice.")
        self._entries[name] = _Entry(description, build)

    @property
    def names(self) -> tuple[str, ...]:
        """Returns the registered names."""
        return tuple(self._entries)

    def get(self, name: str) -> Assistant:
        """Returns an assistant, building it on first use.

        Args:
            name: The assistant name.

        Returns:
            The assistant.

        Raises:
            UnknownAssistant: No assistant has that name.
        """
        if name not in self._built:
            try:
                entry = self._entries[name]
            except KeyError:
                raise UnknownAssistant(name, self.names) from None
            self._built[name] = entry.build()
        return self._built[name]

    def build_all(self) -> AssistantRegistry:
        """Builds every registered assistant.

        Returns:
            The registry.
        """
        for name in self.names:
            self.get(name)
        return self

    def describe(self) -> Mapping[str, str]:
        """Describes the registered assistants.

        Returns:
            The description of each assistant, by name.
        """
        return {name: entry.description for name, entry in self._entries.items()}
