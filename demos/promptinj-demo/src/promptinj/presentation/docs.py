"""The interactive API documentation, with the lab's logo as its icon."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, Response

_LOGO = (Path(__file__).parent / "assets" / "logo.svg").read_bytes()


def register_docs(app: FastAPI) -> None:
    """Serves Swagger UI at `/docs` and the logo at `/logo.svg`.

    The application is created with `docs_url=None`, and this page takes the place of the
    default one.

    Args:
        app: The FastAPI application.
    """

    @app.get("/docs", include_in_schema=False)
    def docs() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=app.title,
            swagger_favicon_url="/logo.svg",
            swagger_ui_parameters=app.swagger_ui_parameters,
        )

    @app.get("/logo.svg", include_in_schema=False)
    def logo() -> Response:
        return Response(_LOGO, media_type="image/svg+xml")
