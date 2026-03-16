FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN set -eux; \
    addgroup --system appgroup; \
    adduser --system --ingroup appgroup --home /app appuser

COPY gateway/requirements.txt /tmp/requirements.txt
RUN python -m pip install --retries 5 --timeout 120 -r /tmp/requirements.txt

COPY gateway/ /app/

USER appuser

EXPOSE 8300

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8300"]
