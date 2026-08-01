"""FastAPI 主入口。

对应实现方案第 9 节 API 轮廓：
- /api/characters, /api/auth/providers, /api/conversations/:id/messages,
  /api/memories, /api/templates, /api/assets/upload-url, /api/generation-tasks,
  /api/characters/:id/timeline, /api/orders, /api/billing/*, /api/payments/:provider/webhook,
  /api/privacy/* 等路由。
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from shared.config import settings

from api.core.error_handlers import (
    app_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from api.core.error_codes import AppError
from api.routers import (
    admin,
    assets,
    auth,
    billing,
    characters,
    conversations,
    generation,
    memories,
    templates,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动与关闭。"""
    # 启动时可预热连接池等
    yield
    # 关闭时释放资源
    from shared.database import engine

    await engine.dispose()


app = FastAPI(
    title="AI 人物陪伴平台 API",
    description="让用户亲手创作、培养并与之长期相处的 AI 人物陪伴产品",
    version="0.1.0",
    lifespan=lifespan,
)

# 统一错误处理：业务异常 → {code, message, params}
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
# 兜底：所有未捕获异常 → 500 + 统一 JSON，并记录完整堆栈
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS：开发环境允许 localhost 直连；生产环境通过 CORS_ORIGINS 环境变量配置前端域名
_default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_cors_env = settings.cors_origins
_cors_origins = _default_origins + [o.strip() for o in _cors_env.split(",") if o.strip()]
if settings.app_env != "development":
    # 生产环境始终允许自身 API 域名与配置的 APP_URL
    for _extra in (settings.app_url, settings.api_url):
        if _extra and _extra not in _cors_origins:
            _cors_origins.append(_extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件：记录每个请求的方法、路径、查询参数、客户端 IP、耗时、状态码
request_logger = logging.getLogger("api.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """把请求详情打到后台日志：方法、路径、查询、客户端 IP、耗时、状态码。"""

    async def dispatch(self, request: Request, call_next):
        # 跳过 /health 这类探活请求，避免日志噪声
        if request.url.path == "/health":
            return await call_next(request)

        start = time.perf_counter()
        client_ip = request.client.host if request.client else "-"
        query = request.url.query
        path_q = f"{request.url.path}?{query}" if query else request.url.path

        # 读取请求体（仅对有 body 的方法做），读取后再塞回以便下游正常消费
        body_bytes = await request.body()

        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request = Request(request.scope, receive)

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            request_logger.exception(
                "%s %s from %s | body=%s | FAILED after %.1fms",
                request.method,
                path_q,
                client_ip,
                self._safe_body(body_bytes),
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        # 5xx 记 ERROR，4xx 记 WARNING，其余 INFO
        log_level = (
            logging.ERROR
            if response.status_code >= 500
            else logging.WARNING if response.status_code >= 400 else logging.INFO
        )
        request_logger.log(
            log_level,
            "%s %s from %s → %d in %.1fms | body=%s",
            request.method,
            path_q,
            client_ip,
            response.status_code,
            elapsed_ms,
            self._safe_body(body_bytes),
        )
        return response

    @staticmethod
    def _safe_body(body_bytes: bytes) -> str:
        """安全展示请求体：空返回 '-'，非文本返回 '<binary %d bytes>'，过长截断。"""
        if not body_bytes:
            return "-"
        try:
            text = body_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return f"<binary {len(body_bytes)} bytes>"
        if len(text) > 1000:
            text = text[:1000] + f"...<truncated {len(text) - 1000} chars>"
        return text


app.add_middleware(RequestLoggingMiddleware)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(characters.router, prefix="/api/characters", tags=["characters"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(memories.router, prefix="/api/memories", tags=["memories"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(generation.router, prefix="/api/generation-tasks", tags=["generation"])
app.include_router(billing.router, prefix="/api", tags=["billing"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "companion-api"}
