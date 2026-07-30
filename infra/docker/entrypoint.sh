#!/bin/bash
set -e

echo "=== 执行数据库迁移 ==="
cd /app/backend && alembic upgrade head

echo "=== 启动 Celery Worker（后台） ==="
cd /app/apps/worker && celery -A app.worker worker -Q image,video,safety,celery -l info &
WORKER_PID=$!

echo "=== 启动 FastAPI ==="
cd /app/apps/api && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &
API_PID=$!

# 优雅退出：任一进程退出则终止全部
trap "echo '收到退出信号，清理进程...'; kill $WORKER_PID $API_PID 2>/dev/null; exit 0" TERM INT

wait -n $API_PID $WORKER_PID
EXIT_CODE=$?
echo "进程退出 (code=$EXIT_CODE)，清理剩余进程..."
kill $WORKER_PID $API_PID 2>/dev/null
exit $EXIT_CODE
