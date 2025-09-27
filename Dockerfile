# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (keep minimal)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates && rm -rf /var/lib/apt/lists/*

# Install Python deps for ingest
COPY requirements-ingest.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-ingest.txt && \
    pip install --no-cache-dir fastapi uvicorn jinja2

# Copy the full repo (ingest CLI expects package layout)
COPY . .
COPY services/ingest/entrypoint.sh /usr/local/bin/ingest-entrypoint
RUN chmod +x /usr/local/bin/ingest-entrypoint

# Default args (overridable via Cloud Run Jobs env)
ENV CHANNELS_CSV=data/channels/islamic_kids.csv \
    OUT_PREFIX=/tmp/out/videos \
    LIMIT=50

# Entrypoint resolves env vars and invokes the ingest CLI
ENTRYPOINT ["/usr/local/bin/ingest-entrypoint"]

