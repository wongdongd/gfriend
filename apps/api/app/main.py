"""FastAPI 主入口。

对应实现方案第 9 节 API 轮廓：
- /api/characters, /api/auth/providers, /api/conversations/:id/messages,
  /api/memories, /api/templates, /api/assets/upload-url, /api/generation-tasks,
  /api/characters/:id/timeline, /api/orders, /api/billing/*, /api/payments/:provider/webhook,
  /api/privacy/* 等路由。
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings

from app.core.error_handlers import app_error_handler, validation_error_handler
from app.core.error_codes import AppError
from app.routers import (
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

# CORS：开发环境允许 localhost 直连；生产环境通过 CORS_ORIGINS 环境变量配置前端域名
import os

_default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_cors_env = os.getenv("CORS_ORIGINS", "")
_cors_origins = _default_origins + [o.strip() for o in _cors_env.split(",") if o.strip()]
if settings.app_env != "development":
    # 生产环境始终允许自身 API 域名与配置的 APP_URL
    for _extra in (os.getenv("APP_URL", ""), os.getenv("API_URL", "")):
        if _extra and _extra not in _cors_origins:
            _cors_origins.append(_extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
