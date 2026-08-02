"""Alembic 环境配置。

使用同步 engine 执行迁移（与运行时的 async engine 分离）。
自动从 ``db.models`` 导入所有模型以支持 autogenerate。
"""
from __future__ import annotations

import os

# 确保 backend/（项目根）在 sys.path 中，使 shared/db 等成为顶层可导入包
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from db.base import Base  # noqa: E402
from db.models import *  # noqa: E402,F401,F403  确保 registry 注册所有模型

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 从环境变量覆盖数据库 URL
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_SYNC_URL", config.get_main_option("sqlalchemy.url")))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：直接执行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
