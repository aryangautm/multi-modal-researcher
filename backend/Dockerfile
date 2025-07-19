FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
COPY backend/requirements.txt ./

RUN uv pip install -r requirements.txt --system


FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install WeasyPrint system dependencies (for text rendering, layout, and images)
# Cleaning up the apt cache in the same RUN layer to reduce image size.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpango-1.0-0 \
       libpangoft2-1.0-0 \
       libgdk-pixbuf-2.0-0 \
       fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY backend/app ./app
COPY backend/workers ./workers