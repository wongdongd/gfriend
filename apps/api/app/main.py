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
from fastapi.middleware.cors import CORSMiddleware

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

# CORS（开发环境允许前端直连）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
