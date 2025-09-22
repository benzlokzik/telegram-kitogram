FROM python:3.12-slim-trixie

# Copy uv and uvx from the official image (per docs)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_PROGRESS=1 \
    UV_NO_WRAP=1 \
    CCACHE_MAXSIZE=500M

WORKDIR /app

# System deps for building native extensions (e.g., fasttext)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
 apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    g++-14 \
    ccache \
    python3-dev \
    --fix-missing \
 && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for better layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies into a project-local virtualenv (.venv)
RUN uv sync --frozen --no-dev

# Copy source code
COPY dialogue_kitogram ./dialogue_kitogram
COPY main.py ./

# Ensure log directories exist (host volume may override)
RUN mkdir -p /app/logs /app/runtime

# Default command: run via uv to use the synced virtualenv
CMD ["uv", "run", "main.py"]
