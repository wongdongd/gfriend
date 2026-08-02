"""Redis-based rate limiting middleware for FastAPI.

Uses a sliding-window approach with Redis sorted sets.
The endpoint path + client IP form the rate-limit key.
"""
from __future__ import annotations

import logging
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# 豁免限流的路径（前缀匹配）
_EXEMPT_PREFIXES = ("/health", "/api/health", "/api/auth/providers", "/api/payments/")

# 豁免限流的精确路径
_EXEMPT_PATHS = {"/api/auth/refresh", "/api/auth/logout"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """滑动窗口限流中间件。"""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self._max_requests = max_requests
        self._window = window_seconds

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 豁免探活、认证信息、Webhook 等路径
        if path in _EXEMPT_PATHS or any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}:{path}"

        try:
            from shared.redis import get_redis

            r = await get_redis()
            now = time.time()
            window_start = now - self._window

            # 使用 sorted set 实现滑动窗口
            pipe = r.pipeline()
            # 移除窗口外的记录
            pipe.zremrangebyscore(key, 0, window_start)
            # 当前窗口内的请求数
            pipe.zcard(key)
            # 添加当前请求
            pipe.zadd(key, {str(now): now})
            # 设置 key 过期时间
            pipe.expire(key, self._window * 2)
            _, count, *_ = await pipe.execute()

            if count > self._max_requests:
                logger.warning("Rate limit exceeded: %s %s (%d/%d)", client_ip, path, count, self._max_requests)
                retry_after = self._window
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "code": "RATE_LIMITED",
                        "message": f"Too many requests. Try again in {retry_after} seconds.",
                        "params": {"retry_after": retry_after},
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception:
            # Redis 不可用时放行，避免阻塞正常流量
            logger.warning("Rate limit check failed, allowing request", exc_info=True)

        return await call_next(request)
