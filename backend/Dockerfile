# =============================================================================
# Multi-stage Docker build for the CodeClash FastAPI backend
#
# Stage 1 (builder): install Python wheels/deps into a relocatable prefix.
# Stage 2 (runtime):  copy prefix (site-packages + console scripts) + app.
# =============================================================================

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /build

# Build deps for packages with native extensions (bcrypt, cryptography, asyncpg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# --prefix installs both:
#   /install/lib/python3.12/site-packages  (importable modules)
#   /install/bin                           (console scripts: uvicorn, alembic, …)
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt


# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:${PATH}"

WORKDIR /app

# Runtime libs only (no compilers)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        docker.io \
        docker-cli \
    && rm -rf /var/lib/apt/lists/*

# Copy full install prefix → merges site-packages AND bin/ into /usr/local
COPY --from=builder /install /usr/local

COPY ./app ./app

# Fail the image build early if dependencies or entrypoints are broken
RUN uvicorn --version \
    && python -c "\
import fastapi, uvicorn, sqlalchemy, asyncpg, alembic, redis, httpx, jose, passlib; \
print('All core dependencies import OK')"

EXPOSE 8000

# Healthcheck is defined in docker-compose.yml for the api service only.
# judge_worker reuses this image but does not expose HTTP.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
