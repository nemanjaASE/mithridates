"""Argument schemas of the tools. Field names and descriptions are shown to the model."""
from pydantic import BaseModel, Field


class GetAccountArgs(BaseModel):
    """Arguments of the `get_account` tool."""

    account_id: str = Field(description="The account id to look up, e.g. u-1001.")
