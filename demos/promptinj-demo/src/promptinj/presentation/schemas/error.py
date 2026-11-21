from pydantic import BaseModel


class ErrorOut(BaseModel):
    """Error response: a generic message, the error id and, where safe, the valid names."""

    error: str
    error_id: str | None = None
    known: list[str] | None = None
