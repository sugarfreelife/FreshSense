FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    MODEL_PATH=/app/models \
    UPLOAD_DIR=/app/uploads

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr passwd \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 freshsense \
    && useradd --system --uid 10001 --gid freshsense --home-dir /home/freshsense --create-home freshsense

WORKDIR /app
COPY requirements-production.lock /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app /app/backend/app
COPY alembic /app/backend/alembic
COPY alembic.ini /app/backend/alembic.ini
RUN mkdir -p /app/uploads /app/models \
    && chown freshsense:freshsense /app/uploads

WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4)"

USER 10001:10001
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
