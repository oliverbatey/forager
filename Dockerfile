FROM python:3.12-slim

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev deps, no virtualenv in container)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev

# Copy application code
COPY forager/ forager/

# ChromaDB data persisted at /data (mounted as a Fly volume)
ENV CHROMA_DATA_DIR=/data/chroma

WORKDIR /app/forager

CMD ["python", "runner.py", "bot"]

