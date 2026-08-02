"""数据库连接管理。

提供异步 engine 与 session factory；``get_db`` 作为 FastAPI 依赖注入。
迁移使用同步 URL（见 ``db/alembic/env.py``）。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


def _normalize_async_url(url: str) -> str:
    """确保异步引擎使用 asyncpg 驱动。

    Railway 的 Postgres 插件注入的 ``DATABASE_URL`` 为 ``postgresql://``
    （同步格式），而 SQLAlchemy 异步引擎需要 ``postgresql+asyncpg://``。
    本地开发默认值已是 ``postgresql+asyncpg://``，这里仅做兼容转换。
    """
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


# 异步 engine（运行时）
engine = create_async_engine(
    _normalize_async_url(settings.database_url),
    echo=False,  # 生产环境禁用 SQL 回显；调试时可在局部设置 echo=True
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
