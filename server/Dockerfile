FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /workspace

COPY server/pyproject.toml server/uv.lock ./server/
RUN uv sync --project ./server --frozen --no-dev --no-install-project

COPY server ./server

ENV PATH="/workspace/server/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port \"${PORT:-8000}\""]