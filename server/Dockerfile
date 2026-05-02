# ─── Base image ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Security: run as non-root
RUN groupadd --gid 1001 kyros \
 && useradd --uid 1001 --gid kyros --shell /bin/bash --create-home kyros

WORKDIR /app

# System dependencies for asyncpg and pgvector
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Install Python dependencies as a separate cached layer
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# ─── Development target ───────────────────────────────────────────────────────
FROM base AS development

COPY --chown=kyros:kyros . .
USER kyros
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "kyros.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ─── Production target ────────────────────────────────────────────────────────
FROM base AS production

COPY --chown=kyros:kyros . .
USER kyros
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production: multiple workers, no reload, access log to stdout
CMD ["uvicorn", "kyros.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log", \
     "--log-level", "info", \
     "--no-use-colors"]
