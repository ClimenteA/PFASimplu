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
RUN mkdir -p /data/db /data/files /app/staticfiles

# Sursele Django (core si app-urile) sunt in /app/src.
ENV PYTHONPATH=/app/src \
    PFASIMPLU_DB_DIR=/data/db \
    PFASIMPLU_MEDIA_ROOT=/data/files \
    PFASIMPLU_LOG_DIR=/data/logs \
    PFASIMPLU_STATIC_ROOT=/app/staticfiles \
    PFASIMPLU_DEBUG=0

# 8000 = aplicatia web (waitress).
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "waitress", "--threads=6", "--listen=*:8000", "core.wsgi:application"]
