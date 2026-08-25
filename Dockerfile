# syntax=docker/dockerfile:1

FROM node:24-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.11.21 AS uv

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/backend/.venv/bin:${PATH}" \
    DATABASE_URI="sqlite:////data/asta-la-vista.sqlite3" \
    APP_HOST="0.0.0.0" \
    APP_PORT="5000" \
    FRONTEND_DIST="/app/frontend" \
    API_TITLE="Asta la Vista API" \
    API_VERSION="v1" \
    OPENAPI_VERSION="3.1.0"

COPY --from=uv /uv /uvx /bin/

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend/ ./
RUN uv sync --locked --no-dev

COPY --from=frontend-build /build/frontend/build /app/frontend
COPY bin/docker-start /usr/local/bin/docker-start

RUN chmod +x /usr/local/bin/docker-start \
    && groupadd --system app \
    && useradd --system --gid app app \
    && mkdir -p /data \
    && chown app:app /data

USER app

EXPOSE 5000

ENTRYPOINT ["docker-start"]
