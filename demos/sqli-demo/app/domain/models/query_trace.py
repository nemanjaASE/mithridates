from dataclasses import dataclass


@dataclass(frozen=True)
class QueryTrace:
    """A statement sent to the database, and its bound parameters."""

    statement: str
    parameters: tuple[str, ...] = ()
