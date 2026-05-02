# V15 — Kyros Zero-Code Memory Proxy Docker Image
#
# Usage:
#   docker build -t kyros-494/proxy -f proxy.Dockerfile .
#   docker run -e KYROS_API_KEY=mk_live_... -e OPENAI_API_KEY=sk-... -p 8080:8080 kyros-494/proxy
#
# Or with docker-compose (add to docker-compose.yml):
#   proxy:
#     build:
#       context: ./server
#       dockerfile: proxy.Dockerfile
#     ports:
#       - "8080:8080"
#     environment:
#       - KYROS_API_KEY=mk_live_...
#       - KYROS_BASE_URL=http://kyros-server:8000
#       - OPENAI_API_KEY=sk-...

FROM python:3.12-slim AS base

WORKDIR /app

# Install only proxy dependencies (minimal image)
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    fastapi>=0.111.0 \
    uvicorn[standard]>=0.30.0 \
    httpx>=0.27.0 \
    pydantic>=2.7.0 \
    pydantic-settings>=2.3.0 \
    structlog>=24.1.0

# Copy only the proxy + shared modules (not ML models)
COPY kyros/__init__.py kyros/
COPY kyros/logging.py kyros/
COPY kyros/proxy/ kyros/proxy/

# Health check
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/proxy/health')" || exit 1

EXPOSE 8080

# Run the proxy
CMD ["python", "-m", "kyros.proxy", "--port", "8080"]
