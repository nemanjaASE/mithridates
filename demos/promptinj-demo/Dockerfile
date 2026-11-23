FROM python:3.14-slim

# Shown by `docker inspect` and Docker Desktop.
LABEL org.opencontainers.image.title="Mithridates: promptinj-demo" \
      org.opencontainers.image.description="Deliberately vulnerable prompt injection demo. Run it on 127.0.0.1 only." \
      org.opencontainers.image.source="https://github.com/nemanjaASE/mithridates" \
      org.opencontainers.image.documentation="https://github.com/nemanjaASE/mithridates/tree/main/demos/promptinj-demo" \
      org.opencontainers.image.licenses="MIT"

# A pinned uv version gives a reproducible build.
COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    # src layout: the package is not installed, it is imported from /app/src.
    PYTHONPATH=/app/src

WORKDIR /app

# Manifest + lock first -> better layer caching; --frozen guarantees the exact versions from uv.lock
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# The prompt .md files are part of the package (assistants/<demo>/prompts) and ship with the code.
COPY src ./src

# Least privilege: the application does not run as root
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "--factory", "promptinj.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
