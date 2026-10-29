# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1 - builder
# Everything needed to *install* the app. This stage is thrown away at the end,
# so pip caches, compilers and build tools never reach the final image.
# =============================================================================
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencies go into an isolated venv, not the system Python.
# Copying a directory between stages is trivial; copying "everything pip
# touched in site-packages" is not.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copied on its own so this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# =============================================================================
# Stage 2 - runtime
# A fresh, minimal image that contains only the interpreter + venv + our code.
# =============================================================================
FROM python:3.13-slim AS runtime

# OCI labels: metadata registries and scanners can read without pulling layers.
LABEL org.opencontainers.image.title="calculator" \
      org.opencontainers.image.description="Calculator service: FastAPI + Prometheus metrics" \
      org.opencontainers.image.source="https://github.com/OWNER/REPO" \
      org.opencontainers.image.licenses="MIT"

# PYTHONUNBUFFERED: logs appear immediately in `docker logs` instead of being
# buffered. Without it your logs arrive in bursts and look delayed.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    PORT=8000

# Unprivileged user. Never run app code as root: if the process is compromised,
# the attacker gets a nobody-level account, not the container's root.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

# Bring in the finished venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# --chown so the runtime user owns the files (no need for root at start).
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser static ./static

USER appuser

# Documentation only - EXPOSE does not publish anything. `docker run -p` does
EXPOSE 8000

# Docker runs this inside the container every 30s and marks the container
# healthy/unhealthy. Uses the stdlib because slim images have no curl.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"

# sh -c is needed to expand ${PORT}. `exec` replaces the shell with uvicorn so
# uvicorn becomes PID 1 and receives SIGTERM directly -> graceful shutdown.
# --proxy-headers lets it trust X-Forwarded-* when it sits behind a proxy.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
