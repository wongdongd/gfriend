# Worker 服务生产 Dockerfile
# Railway 构建：Root Directory = /, Dockerfile path = infra/docker/worker.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY apps/worker/ /app/apps/worker/

ENV PYTHONPATH=/app/backend

CMD ["celery", "-A", "app.worker", "worker", "-Q", "image,video,safety,celery", "-l", "info"]

WORKDIR /app/apps/worker
