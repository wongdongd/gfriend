# Backend 单镜像（FastAPI + Celery Worker 合并）
# backend 作为一个普通 Python 项目，直接 python main.py 启动
# Railway 构建：Root Directory = /, Dockerfile path = infra/docker/backend.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖（利用 Docker 层缓存）
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 复制整个 backend 项目（shared/db/companion_core/provider_adapters/api/worker + main.py）
COPY backend/ /app/

# backend 项目根即 /app，子包为顶层包；PYTHONPATH 确保容器内任意 CWD 都能导入
ENV PYTHONPATH=/app
ENV APP_ROLE=api
ENV PORT=8000

# 启动脚本：先迁移，再同时启动 API + Worker
COPY infra/docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
EXPOSE 8000
