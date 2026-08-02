"""AI 人物陪伴平台 - 后端统一入口。

用法：
    python main.py              # 默认启动 API（uvicorn）
    python main.py api          # 显式启动 API
    python main.py worker       # 启动 Celery Worker
    python main.py beat         # 启动 Celery Beat 调度器（Windows 必须独立进程）
    python main.py migrate      # 执行数据库迁移（alembic upgrade head）

环境变量：
    APP_ROLE=api|worker|beat|migrate  # 等价于命令行参数，用于容器单入口部署
    PORT=8000                          # API 监听端口
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")  # 始终加载 backend/.env，不依赖启动目录


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
    """启动 Celery Worker。

    Windows 下 billiard 的 prefork pool 会在 SpawnPoolWorker 阶段抛
    PermissionError(13, '拒绝访问。')——这是 Celery 5.x 在 Windows 上的已知问题，
    因为 billiard 的子进程句柄传递依赖 POSIX 语义。这里在 Windows 上自动切到 solo
    pool（单进程同步执行），Linux/macOS 仍用默认 prefork。

    注意：Celery 在 Windows 上禁止 -B/--beat 内嵌到 worker，Beat 必须独立进程运行。
    本地开发请额外开一个终端执行 `python main.py beat`。
    POSIX 上若需内嵌可设 CELERY_EMBED_BEAT=1（仅开发用，生产应独立 beat 进程）。
    """
    from worker.celery_app import app  # noqa: F401  确保任务注册

    queues = os.getenv("CELERY_QUEUES", "image,video,safety,celery")
    log_level = os.getenv("CELERY_LOG_LEVEL", "info")
    # POSIX 开发环境可选内嵌 beat；Windows 永不内嵌（Celery 会直接拒绝并报错）
    embed_beat = (
        os.getenv("CELERY_EMBED_BEAT", "0") == "1"
        and not sys.platform.startswith("win")
    )

    argv = ["worker", "-Q", queues, "-l", log_level]
    if sys.platform.startswith("win"):
        # Windows：禁用 prefork，改用 solo pool（单进程，无子进程，避免 PermissionError）
        argv.extend(["--pool", "solo"])
    else:
        # POSIX：可使用 prefork，并发数由环境变量控制
        concurrency = os.getenv("CELERY_CONCURRENCY")
        if concurrency:
            argv.extend(["--concurrency", concurrency])

    if embed_beat:
        argv.append("--beat")
        argv.extend(["--schedule", os.getenv("CELERY_BEAT_SCHEDULE_PATH", "celerybeat-schedule")])

    app.worker_main(argv)


def run_beat() -> None:
    """启动 Celery Beat 调度器（独立进程）。

    Windows 下 Celery 不允许 -B 嵌入 worker，必须独立运行 beat。
    本地开发：开两个终端，分别 `python main.py worker` 和 `python main.py beat`。
    """
    from worker.celery_app import app  # noqa: F401  确保任务注册

    log_level = os.getenv("CELERY_LOG_LEVEL", "info")
    schedule_path = os.getenv("CELERY_BEAT_SCHEDULE_PATH", "celerybeat-schedule")

    app.start(
        [
            "beat",
            "--loglevel",
            log_level,
            "--schedule",
            schedule_path,
        ]
    )


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
    "beat": run_beat,
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
