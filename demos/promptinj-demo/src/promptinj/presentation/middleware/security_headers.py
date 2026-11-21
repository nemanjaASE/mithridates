"""Adds HTTP security headers to every response."""
from fastapi import FastAPI, Request

_BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}
_API_CSP = "default-src 'none'; frame-ancestors 'none'"

# Swagger UI loads scripts from a CDN, so a strict CSP would break it.
_DOCS_PATHS = ("/docs", "/redoc")


def register_security_headers(app: FastAPI) -> None:
    """Registers the middleware that sets the security headers.

    Args:
        app: The FastAPI application.
    """
    @app.middleware("http")
    async def _add_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(_BASE_HEADERS)
        if not request.url.path.startswith(_DOCS_PATHS):
            response.headers["Content-Security-Policy"] = _API_CSP
        return response
