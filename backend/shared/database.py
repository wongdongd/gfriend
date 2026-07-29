"""数据库连接管理。

提供异步 engine 与 session factory；``get_db`` 作为 FastAPI 依赖注入。
迁移使用同步 URL（见 ``db/alembic/env.py``）。
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import settings

# 异步 engine（运行时）
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 异步 session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：提供数据库会话，请求结束自动关闭。"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
