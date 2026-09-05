FROM python:3.12-slim-trixie

# Copy uv and uvx from the official image (per docs)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_PROGRESS=1 \
    UV_NO_WRAP=1 \
    HF_HOME=/app/runtime/huggingface \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

WORKDIR /app

# Git installs the pinned spam-detector release; libgomp supports CPU PyTorch.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
 apt-get update \
 && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for better layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies into a project-local virtualenv (.venv)
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

# Copy source code
COPY dialogue_kitogram ./dialogue_kitogram
COPY main.py ./

# Ensure log directories exist (host volume may override)
RUN mkdir -p /app/logs /app/runtime

# Use installed dependencies without resolving or installing at startup.
CMD ["/app/.venv/bin/python", "main.py"]
