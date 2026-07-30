# API 服务生产 Dockerfile
# Railway 构建：Root Directory = /, Dockerfile path = infra/docker/api.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 依赖层（利用 Docker 缓存）
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 复制代码
COPY backend/ /app/backend/
COPY apps/api/ /app/apps/api/

ENV PYTHONPATH=/app/backend
ENV APP_PORT=8000

# 启动前自动执行数据库迁移
CMD ["sh", "-c", "\
  cd /app/backend && alembic upgrade head && \
  cd /app/apps/api && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

EXPOSE 8000
