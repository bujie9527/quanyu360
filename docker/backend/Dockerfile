FROM python:3.11-slim-bookworm AS base

ARG SERVICE_PATH
ARG DEBIAN_MIRROR
ARG DEBIAN_SECURITY_MIRROR
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL} \
    PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST} \
    PYTHONPATH=/app:/app/backend:/app/agent-runtime:/app/workflow-engine

WORKDIR /app

RUN set -eux; \
    addgroup --system appgroup; \
    adduser --system --ingroup appgroup --home /app appuser

COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --retries 5 --timeout 120 --prefer-binary -r /tmp/requirements.txt

COPY --chown=appuser:appgroup backend /app/backend
COPY --chown=appuser:appgroup agent-runtime /app/agent-runtime
COPY --chown=appuser:appgroup workflow-engine /app/workflow-engine
COPY --chown=appuser:appgroup tools /app/tools

WORKDIR /app/${SERVICE_PATH}

USER appuser
