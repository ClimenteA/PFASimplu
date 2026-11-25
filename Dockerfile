FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app

# uv pentru instalarea dependintelor din uv.lock (fara dev/pyinstaller).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

# Directoarele de date (montate ca volume in docker-compose).
RUN mkdir -p /data/dbsqlite /data/media /app/staticfiles

# Sursele Django (core, app-urile, mcp_server) sunt in /app/src.
ENV PYTHONPATH=/app/src \
    PFASIMPLU_DB_DIR=/data/dbsqlite \
    PFASIMPLU_MEDIA_ROOT=/data/media \
    PFASIMPLU_STATIC_ROOT=/app/staticfiles \
    PFASIMPLU_DEBUG=0 \
    PFASIMPLU_MCP_PORT=8001

# 8000 = aplicatia web (waitress), 8001 = serverul MCP (uvicorn/FastMCP).
EXPOSE 8000 8001

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "waitress", "--threads=6", "--listen=*:8000", "core.wsgi:application"]
