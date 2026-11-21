"""Login request model."""
from pydantic import BaseModel, Field

MAX_INPUT_LENGTH = 128


class LoginIn(BaseModel):
    """Credentials submitted to the login endpoint, with bounded lengths."""

    username: str = Field(min_length=1, max_length=MAX_INPUT_LENGTH)
    password: str = Field(min_length=1, max_length=MAX_INPUT_LENGTH)
