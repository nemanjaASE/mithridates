"""Per-request context passed to the agent. Tools read the user id from it, not from the model."""
from pydantic import BaseModel


class AgentContext(BaseModel):
    """Per-request facts a tool may trust."""

    current_user_id: str
