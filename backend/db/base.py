"""SQLAlchemy 声明式基类与公共 Mixin。

所有模型继承自 ``Base``；``TimestampMixin`` 提供 ``created_at`` / ``updated_at``
两列；``UUIDPrimaryKey`` 提供名为 ``id`` 的 UUID 主键；
``SoftDeleteMixin`` 提供统一的软删除能力。
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类。"""


class UUIDPrimaryKey:
    """UUID 主键 Mixin，列名 ``id``，默认生成 UUID4。"""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """创建/更新时间戳 Mixin。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """统一软删除 Mixin。

    模型添加此 Mixin 后获得 ``is_deleted`` 和 ``deleted_at`` 字段。
    所有查询应在 WHERE 子句中过滤 ``is_deleted == False``，除非需要审计视角。
    """

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def soft_delete(self) -> None:
        """标记为已删除（设置时间戳）。"""
        self.is_deleted = True
        self.deleted_at = datetime.now(tz=UTC)
