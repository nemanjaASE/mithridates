"""Maps application errors to HTTP responses with a generic message and an error id."""
import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..domain.errors import InvalidTokenError, StoreUnavailable
from .schemas import ErrorOut

_logger = logging.getLogger("app.errors")


def _json(status_code: int, body: ErrorOut, headers: dict[str, str] | None = None) -> JSONResponse:
    """Returns the error as a JSON response."""
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True), headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    """Registers the exception handlers on the application.

    Args:
        app: The FastAPI application.
    """
    @app.exception_handler(InvalidTokenError)
    async def _invalid_token(_: Request, exc: InvalidTokenError) -> JSONResponse:
        # The reason (expired, bad signature) goes to the server log only.
        reason = type(exc.__cause__).__name__ if exc.__cause__ else "missing_bearer_header"
        _logger.info("token_rejected reason=%s", reason)
        return _json(
            status.HTTP_401_UNAUTHORIZED,
            ErrorOut(error="Invalid or expired authentication token."),
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    @app.exception_handler(StoreUnavailable)
    async def _store_unavailable(_: Request, exc: StoreUnavailable) -> JSONResponse:
        error_id = uuid.uuid4().hex
        _logger.warning("store_unavailable error_id=%s cause=%r", error_id, exc.__cause__)
        return _json(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorOut(error="The service is temporarily unavailable.", error_id=error_id),
        )

    @app.exception_handler(RequestValidationError)
    async def _invalid_input(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI's default response echoes the submitted input; this one names the fields only.
        fields = [".".join(str(p) for p in err["loc"]) for err in exc.errors()]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"error": "Invalid input.", "fields": fields},
        )

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        error_id = uuid.uuid4().hex
        _logger.error("unexpected_error error_id=%s", error_id, exc_info=exc)
        return _json(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorOut(error="Internal server error.", error_id=error_id))
