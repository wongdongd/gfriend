# API + Worker 共用 Dockerfile（基于同一 Python 镜像）
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 复制后端内核
COPY backend/ /app/backend/

# 设置 PYTHONPATH
ENV PYTHONPATH=/app/backend

# 复制 API 与 Worker 代码
COPY apps/api/ /app/apps/api/
COPY apps/worker/ /app/apps/worker/

EXPOSE 8000
