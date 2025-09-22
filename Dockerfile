FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for building native extensions (e.g., fasttext)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
 && rm -rf /var/lib/apt/lists/*

# Install uv (ultra-fast Python package manager)
RUN pip install --no-cache-dir uv

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
CMD ["uv", "run", "python", "main.py"]
