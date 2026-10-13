# Kin service image (kin API for the Hermes plugin: intake, retrieval, scheduler). uv-managed, lockfile-driven.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY kin ./kin
COPY config ./config
COPY locale ./locale
COPY fixtures ./fixtures
COPY README.md ./
RUN uv sync --frozen --no-dev

RUN mkdir -p /app/data
VOLUME ["/app/data"]
EXPOSE 8765

ENTRYPOINT ["kin"]
CMD ["--help"]
