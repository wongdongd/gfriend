"""Celery 异步工具：在同步任务中安全调用异步代码。

所有 Celery 任务共享同一个 runner；每个任务调用处不再重复创建/关闭事件循环。
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any

# 线程本地存储 —— 每个线程最多持有一个事件循环
_local = threading.local()


def run_async(coro: Any) -> Any:
    """在同步上下文中运行一个协程并返回结果。

    Celery 任务函数是同步的，但我们的业务逻辑大量使用 async/await。
    此函数为每个线程缓存一个事件循环，避免每次都 new/close。
    """
    loop = getattr(_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _local.loop = loop
    return loop.run_until_complete(coro)
