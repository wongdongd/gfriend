"""统一日志配置：写入文件 + 按时间滚动 + 同时保留控制台输出。

设计原则：
- **永不阻塞应用启动**：文件日志初始化失败时只打 stderr 警告，
  控制台日志照常工作，应用继续运行。
- 幂等：多次调用不会重复添加 handler。

滚动策略（TimedRotatingFileHandler）：
- 按天滚动（"midnight"）：每天零点切换日志文件
- 保留 LOG_BACKUP_DAYS 天内的文件，更早的自动删除
- 滚动时旧文件 gzip 压缩为 .gz

用法：
    在 shared/__init__.py 中调用 setup_logging()，API / Worker / 迁移都会自动生效。
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_LOG_CONFIGURED = False


def _formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _try_make_file_handler(log_dir: Path) -> TimedRotatingFileHandler | None:
    """尝试创建文件 handler；失败返回 None（应用仍可只用控制台日志继续运行）。"""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        # 验证可写
        test_file = log_dir / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except (OSError, PermissionError) as e:
        print(f"[logging] 无法写入日志目录 {log_dir}: {e}，回退到仅控制台输出", file=sys.stderr)
        return None

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    when = os.getenv("LOG_WHEN", "midnight")
    backup = int(os.getenv("LOG_BACKUP_DAYS", "14"))
    compress = os.getenv("LOG_COMPRESS", "1") == "1"

    try:
        handler = TimedRotatingFileHandler(
            filename=str(log_dir / "backend.log"),
            when=when,
            interval=1,
            backupCount=backup,
            encoding="utf-8",
            utc=False,
        )
        handler.suffix = "%Y-%m-%d"
        if compress:
            handler.namer = lambda name: name if name.endswith(".gz") else name + ".gz"
            handler.rotator = _gzip_rotate
        handler.setLevel(level)
        handler.setFormatter(_formatter())
        return handler
    except Exception as e:  # noqa: BLE001 - 初始化失败不应阻塞应用
        print(f"[logging] 创建文件 handler 失败: {e}，回退到仅控制台输出", file=sys.stderr)
        return None


def _gzip_rotate(source: str, dest: str) -> None:
    """滚动时把旧日志文件压缩成 .gz。

    Windows 下文件可能仍被 handler 持有句柄，os.remove 会报 WinError 32，
    此时跳过删除（.gz 已生成，残留的 source 会在下次滚动或进程退出时清理）。
    """
    import gzip
    import shutil
    import time

    gz_path = dest if dest.endswith(".gz") else dest + ".gz"
    if os.path.exists(gz_path):
        try:
            os.remove(gz_path)
        except OSError:
            pass
    try:
        with open(source, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    except OSError:
        return
    # Windows 下 source 可能仍被占用，重试几次再放弃
    for _ in range(5):
        try:
            os.remove(source)
            return
        except PermissionError:
            time.sleep(0.1)


def _log_dir() -> Path:
    """确定日志目录：优先 LOG_DIR；默认容器 /var/log/companion，失败回退到 ./logs。"""
    env_dir = os.getenv("LOG_DIR")
    if env_dir:
        return Path(env_dir)
    return Path("/var/log/companion")


def setup_logging() -> None:
    """初始化根 logger：控制台 + 文件（按时间滚动，可选）。

    幂等：多次调用不会重复添加 handler。
    安全：文件日志初始化失败时，控制台日志仍工作，应用继续运行。
    """
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    root = logging.getLogger()
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root.setLevel(level)

    # 控制台 handler（容器/终端可见，这是保底输出，永远添加）
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(_formatter())
    root.addHandler(console)

    # 文件 handler（按时间滚动，失败则跳过）
    log_dir = _log_dir()
    file_handler = _try_make_file_handler(log_dir)
    if file_handler is not None:
        root.addHandler(file_handler)
        root.info("日志已初始化 -> 文件: %s + 控制台", log_dir / "backend.log")
    else:
        # 回退：尝试本地 ./logs 目录
        fallback_dir = Path("logs")
        file_handler = _try_make_file_handler(fallback_dir)
        if file_handler is not None:
            root.addHandler(file_handler)
            root.info("日志已初始化 -> 文件: %s + 控制台（回退目录）", fallback_dir / "backend.log")
        else:
            root.info("日志已初始化 -> 仅控制台输出（文件不可写）")

    _LOG_CONFIGURED = True

    # Uvicorn 的 logger 默认 propagate=False，需要显式添加相同的 handler
    for uv_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(uv_name)
        uv_logger.setLevel(level)
        for h in root.handlers:
            if h not in uv_logger.handlers:
                uv_logger.addHandler(h)
