#!/bin/bash
set -e

# 迁移失败不阻塞 API 启动（记录日志，健康检查仍可通过对 /health 的探测）
echo "=== 执行数据库迁移 ==="
python main.py migrate || echo "[WARN] 数据库迁移失败，继续启动服务（可能缺少 DATABASE_URL 或数据库未就绪）"

echo "=== 启动 Celery Worker（后台） ==="
# worker 失败不拖垮 API：失败只记录日志，不再触发整个容器退出
APP_ROLE=worker python main.py &
WORKER_PID=$!

echo "=== 启动 FastAPI（主进程） ==="
APP_ROLE=api python main.py &
API_PID=$!

# 优雅退出：API 是主进程，worker 退出不影响 API
trap "echo '收到退出信号，清理进程...'; kill $WORKER_PID $API_PID 2>/dev/null; exit 0" TERM INT

# 只监听 API 进程。worker 退出仅打日志；API 退出则整个容器退出
while kill -0 $API_PID 2>/dev/null; do
    if ! kill -0 $WORKER_PID 2>/dev/null; then
        echo "[WARN] Worker 已退出（code 可能因 Redis 未配置），但 API 继续运行"
        # 只记录一次
        WORKER_PID=0
    fi
    sleep 2
done

echo "API 进程已退出，清理 Worker..."
kill $WORKER_PID $API_PID 2>/dev/null
wait $API_PID
exit $?
