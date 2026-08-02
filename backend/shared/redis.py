"""Redis 连接工具。

提供异步 Redis 客户端，支持 token 黑白名单、限流计数器等场景。
"""
from __future__ import annotations

import redis.asyncio as aioredis

from shared.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """获取全局 Redis 异步连接（惰性初始化）。"""
    global _redis
    if _redis is not None:
        return _redis
    _redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis


async def close_redis() -> None:
    """关闭 Redis 连接（用于应用 shutdown）。"""
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
