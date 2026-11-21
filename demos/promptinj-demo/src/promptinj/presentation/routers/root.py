from collections.abc import Mapping

from fastapi import APIRouter

from .prefix import API_PREFIX


def build_root_router(backend: Mapping[str, str], assistants: Mapping[str, str]) -> APIRouter:
    """Builds the router for `GET /`.

    Args:
        backend: The adapters in use, by component.
        assistants: The description of each assistant, by name.

    Returns:
        The configured router.
    """
    router = APIRouter()

    @router.get("/")
    def root() -> dict:
        """Lists the endpoints, the adapters and the assistants."""
        endpoints = [f"POST {API_PREFIX}/auth/login"]
        # One entry per registered assistant, so what is actually wired is visible
        # without reading the source — including anything added since.
        endpoints += [
            f"POST {API_PREFIX}/{name.replace('-', '/', 1)}  (Authorization: Bearer <token>)"
            for name in assistants
        ]
        return {
            "lab": "LLM prompt injection demo — account assistant",
            "warning": "Deliberately vulnerable. Run locally, for education only.",
            "backend": dict(backend),
            "assistants": dict(assistants),
            "endpoints": endpoints,
            "swagger": "/docs",
        }

    return router
