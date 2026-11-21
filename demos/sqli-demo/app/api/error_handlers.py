"""Maps application errors to HTTP responses with a generic message and an error id."""
import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..domain.errors import InvalidTokenError, QueryExecutionError, StoreUnavailable
from .schemas import DebugTraceOut, ErrorOut

_logger = logging.getLogger("app.errors")


def _json(status_code: int, body: ErrorOut, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True), headers=headers)


def register_error_handlers(app: FastAPI, expose_query_trace: bool) -> None:
    """Registers the exception handlers on the application.

    Args:
        app: The FastAPI application.
        expose_query_trace: Whether a failed query's SQL is included in the response.
    """
    @app.exception_handler(QueryExecutionError)
    async def _query_failed(_: Request, exc: QueryExecutionError) -> JSONResponse:
        error_id = uuid.uuid4().hex
        _logger.warning("query_failed error_id=%s cause=%r", error_id, exc.__cause__)
        debug = DebugTraceOut.from_trace(exc.trace, expose_query_trace)
        # Generic on purpose: no "SQL"/"query" wording that would confirm an injection point to an attacker.
        return _json(
            status.HTTP_400_BAD_REQUEST,
            ErrorOut(error="The request could not be processed.", error_id=error_id, debug=debug),
        )

    @app.exception_handler(StoreUnavailable)
    async def _store_unavailable(_: Request, exc: StoreUnavailable) -> JSONResponse:
        # A dependency is unreachable, the caller can retry, and nothing about the
        # database reaches the response body.
        error_id = uuid.uuid4().hex
        _logger.warning("store_unavailable error_id=%s cause=%r", error_id, exc.__cause__)
        return _json(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorOut(error="The service is temporarily unavailable.", error_id=error_id),
        )

    @app.exception_handler(InvalidTokenError)
    async def _invalid_token(_: Request, exc: InvalidTokenError) -> JSONResponse:
        # The reason (expired, bad signature...) goes only to the server log, never to the client.
        reason = type(exc.__cause__).__name__ if exc.__cause__ else "missing_bearer_header"
        _logger.info("token_rejected reason=%s", reason)
        # A 401 for a bearer token carries a WWW-Authenticate header.
        return _json(
            status.HTTP_401_UNAUTHORIZED,
            ErrorOut(error="Invalid or expired authentication token."),
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    @app.exception_handler(RequestValidationError)
    async def _invalid_input(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI's default response echoes the submitted input (e.g. the password) — we don't want that.
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
