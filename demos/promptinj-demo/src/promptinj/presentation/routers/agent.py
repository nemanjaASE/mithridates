"""Agent endpoint. Statuses: 200 answered, 401 missing or invalid token, 404 unknown variant,
503 model or store unreachable, 422 invalid input.
"""
from collections.abc import Callable

from fastapi import APIRouter, Depends, status

from ...application.use_cases import AskAssistantUseCase
from ...domain.entities import Variant
from ..schemas import AgentAnswerOut, ErrorOut, QuestionIn
from .prefix import API_PREFIX

FEATURE = "agent"

_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut, "description": "Missing or invalid token"},
    status.HTTP_404_NOT_FOUND: {"model": ErrorOut, "description": "No such assistant"},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorOut, "description": "Dependency unreachable"},
}


def build_agent_router(
    ask: AskAssistantUseCase,
    current_user_id: Callable[..., str],
    expose_tool_trace: bool,
) -> APIRouter:
    """Builds the router for `POST /agent/{variant}`.

    Args:
        ask: The use case that runs an assistant.
        current_user_id: Dependency that returns the user id from the token.
        expose_tool_trace: Whether the tool calls are included in the response.

    Returns:
        The configured router.
    """
    router = APIRouter(prefix=API_PREFIX, tags=[FEATURE])

    @router.post(
        f"/{FEATURE}/{{variant}}",
        response_model=AgentAnswerOut,
        response_model_exclude_none=True,
        responses=_RESPONSES,
    )
    def answer(variant: Variant, body: QuestionIn, user_id: str = Depends(current_user_id)) -> AgentAnswerOut:
        """Answers a question with the agent of the given variant."""
        result = ask.execute(f"{FEATURE}-{variant.value}", body.question, user_id)
        return AgentAnswerOut.from_result(result, expose_tool_trace)

    return router
