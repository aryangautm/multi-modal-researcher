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

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY backend/app ./app
COPY backend/workers ./workers