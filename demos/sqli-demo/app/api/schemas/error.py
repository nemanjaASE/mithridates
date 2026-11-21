from pydantic import BaseModel

from .trace import DebugTraceOut


class ErrorOut(BaseModel):
    """Error response: a generic message and the error id."""

    error: str
    error_id: str | None = None
    debug: DebugTraceOut | None = None
