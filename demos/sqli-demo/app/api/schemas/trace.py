from pydantic import BaseModel

from ...domain.models import QueryTrace


class DebugTraceOut(BaseModel):
    """The executed SQL, returned only when EXPOSE_QUERY_TRACE is on."""

    statement: str
    parameters: list[str] | None = None

    @classmethod
    def from_trace(cls, trace: QueryTrace, expose: bool) -> "DebugTraceOut | None":
        """Builds the trace for the response.

        Args:
            trace: The statement that reached the database.
            expose: Whether the trace may be returned.

        Returns:
            The trace, or None when it may not be returned.
        """
        if not expose:
            return None
        return cls(statement=trace.statement, parameters=list(trace.parameters) or None)
