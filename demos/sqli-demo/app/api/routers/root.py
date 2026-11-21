from fastapi import APIRouter

from ...domain.models import Variant
from .prefix import API_PREFIX


def build_root_router(debug_enabled: bool) -> APIRouter:
    """Builds the router for `GET /`.

    Args:
        debug_enabled: Whether the debug endpoint is listed.

    Returns:
        The configured router.
    """
    router = APIRouter()

    @router.get("/")
    def root() -> dict:
        """Lists the available endpoints."""
        endpoints = [f"POST {API_PREFIX}/{v.value}/auth/login" for v in Variant]
        endpoints.append(f"GET {API_PREFIX}/users/me  (Authorization: Bearer <token>)")
        if debug_enabled:
            endpoints.append(f"GET {API_PREFIX}/debug/users")
        return {
            "lab": "SQL injection demo",
            "warning": "Deliberately vulnerable. Run locally, for education only.",
            "endpoints": endpoints,
            "swagger": "/docs",
        }

    return router
