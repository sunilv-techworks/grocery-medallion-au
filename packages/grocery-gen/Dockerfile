# syntax=docker/dockerfile:1.7

FROM python:3.11-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /uvx /bin/

WORKDIR /app

# Copy workspace metadata first for better caching
COPY pyproject.toml uv.lock ./
COPY packages/grocery-gen/pyproject.toml packages/grocery-gen/pyproject.toml
COPY packages/grocery-mcp/pyproject.toml packages/grocery-mcp/pyproject.toml
COPY packages/grocery-forecast/pyproject.toml packages/grocery-forecast/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package grocery-gen

# Now copy the source and install the package itself
COPY packages/grocery-gen/src packages/grocery-gen/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package grocery-gen

# ---- Runtime stage ----
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/packages/grocery-gen /app/packages/grocery-gen

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["grocery-gen"]
CMD ["--help"]
