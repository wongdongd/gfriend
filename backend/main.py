"""AI 人物陪伴平台 - 后端统一入口。

用法：
    python main.py              # 默认启动 API（uvicorn）
    python main.py api          # 显式启动 API
    python main.py worker       # 启动 Celery Worker
    python main.py migrate      # 执行数据库迁移（alembic upgrade head）

环境变量：
    APP_ROLE=api|worker|migrate  # 等价于命令行参数，用于容器单入口部署
    PORT=8000                    # API 监听端口
"""
from __future__ import annotations

import os
import subprocess
import sys


def run_api() -> None:
    """启动 FastAPI（uvicorn）。"""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("APP_ENV") == "development",
        reload_dirs=["api", "shared", "db", "companion_core", "provider_adapters", "worker"],
    )


def run_worker() -> None:
    """启动 Celery Worker。"""
    from celery import Celery

    from worker.celery_app import app  # noqa: F401  确保任务注册

    queues = os.getenv("CELERY_QUEUES", "image,video,safety,celery")
    app.worker_main(["worker", "-Q", queues, "-l", os.getenv("CELERY_LOG_LEVEL", "info")])


def run_migrate() -> None:
    """执行数据库迁移（alembic upgrade head）。"""
    from alembic.config import CommandLine
    from alembic.config import Config

    cli = CommandLine()
    cli.parser.add_argument("-c", "--config", default="alembic.ini", help="alembic 配置文件")
    options = cli.parser.parse_args(["upgrade", "head"])
    config = Config(options.config)
    cli.run_cmd(config, options)


COMMANDS = {
    "api": run_api,
    "worker": run_worker,
    "migrate": run_migrate,
}


def main() -> None:
    role = sys.argv[1] if len(sys.argv) > 1 else os.getenv("APP_ROLE", "api")
    cmd = COMMANDS.get(role)
    if cmd is None:
        print(f"未知命令: {role}", file=sys.stderr)
        print(f"可用命令: {', '.join(COMMANDS)}（或设置 APP_ROLE 环境变量）", file=sys.stderr)
        sys.exit(1)
    cmd()


if __name__ == "__main__":
    main()
