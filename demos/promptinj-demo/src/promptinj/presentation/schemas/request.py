from pydantic import BaseModel, Field

# Bounded, so one request cannot send an unlimited number of tokens.
MAX_QUESTION_LENGTH = 2000


class QuestionIn(BaseModel):
    """A question for an assistant, with a bounded length."""

    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
