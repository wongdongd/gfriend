# API + Worker 合并 Dockerfile
# 一个容器同时跑 FastAPI 和 Celery Worker，MVp 阶段无需拆分
# Railway 构建：Root Directory = /, Dockerfile path = infra/docker/api.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY apps/api/ /app/apps/api/
COPY apps/worker/ /app/apps/worker/

ENV PYTHONPATH=/app/backend
ENV APP_PORT=8000

# 启动脚本：先跑数据库迁移，再同时启动 FastAPI + Celery Worker
COPY infra/docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
EXPOSE 8000
