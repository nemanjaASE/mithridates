FROM python:3.13-slim

# Shown by `docker inspect` and Docker Desktop.
LABEL org.opencontainers.image.title="Mithridates: __NAME__" \
      org.opencontainers.image.description="Deliberately vulnerable __TITLE__ demo. Run it on 127.0.0.1 only." \
      org.opencontainers.image.source="https://github.com/nemanjaASE/mithridates" \
      org.opencontainers.image.documentation="https://github.com/nemanjaASE/mithridates/tree/main/demos/__NAME__" \
      org.opencontainers.image.licenses="MIT"

# A pinned uv version gives a reproducible build.
COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Manifest and lock first, for layer caching; --frozen installs exactly what uv.lock pins.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app

# The application does not run as root.
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "--factory", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
