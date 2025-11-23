# Stage 1: Builder - Compilation et installation dependencies
FROM python:3.13-slim AS builder

# Copier binaire uv depuis image officielle (eviter installation manuelle)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Variables environnement builder pour optimisation uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never

# Repertoire de travail standardise
WORKDIR /app

# Copier fichiers dependencies (separation layer cache)
COPY pyproject.toml uv.lock ./

# Installer dependencies avec cache mount (sans projet)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copier code source apres dependencies
COPY app/ ./app/

# Installer projet complet
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Installer Playwright browsers et dependances systeme pour crawl4ai
RUN .venv/bin/crawl4ai-setup

# Stage 2: Runtime - Image finale propre et legere
FROM python:3.13-slim AS runtime

# Installer dependances systeme Playwright pour headless mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    ca-certificates \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Creer utilisateur non-root pour securite
RUN adduser --disabled-password --gecos "" --uid 1000 appuser

# Definir WORKDIR et copier depuis builder avec permissions correctes
WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app /app

# Copier cache Playwright depuis builder
COPY --from=builder --chown=appuser:appuser /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright

# Changer vers utilisateur non-root
USER appuser

# Variables environnement runtime
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Exposer port application
EXPOSE 8000

# Healthcheck natif Docker
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Commande demarrage production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
