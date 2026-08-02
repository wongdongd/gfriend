"""记忆模型（含 pgvector 向量检索）。

对应实现方案第 4 节、第 6 节：
- 记忆不可静默持久化：候选记忆必须有确认状态，用户能够逐条撤销。
- 只在用户和当前角色的命名空间检索记忆，默认最多注入少量高相关条目。
- 对敏感信息默认不自动保存，要求显式确认。
- 删除操作同时删除向量和原文。
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKey

# pgvector：若环境未安装 pgvector 包，回退为普通列，保证 import 不报错
try:
    from pgvector.sqlalchemy import Vector
    _HAS_PGVECTOR = True
except ImportError:  # pragma: no cover
    Vector = None  # type: ignore[assignment, misc]
    _HAS_PGVECTOR = False

# 嵌入维度，与 .env 的 EMBEDDING_DIM 对齐；可按供应商调整
EMBEDDING_DIM = 1536

if TYPE_CHECKING:
    from db.models.character import Character


class MemoryType(str, enum.Enum):
    """记忆类型。"""

    PREFERENCE = "preference"  # 用户偏好
    EVENT = "event"  # 共同事件
    RELATIONSHIP = "relationship"  # 关系信息
    IMPORTANT_DATE = "important_date"  # 重要日期
    FACT = "fact"  # 其他事实


class MemoryStatus(str, enum.Enum):
    """记忆确认状态 —— 记忆不可静默持久化的关键。"""

    CANDIDATE = "candidate"  # 候选：系统提取，等待用户确认
    CONFIRMED = "confirmed"  # 已确认：可注入上下文
    REJECTED = "rejected"  # 已拒绝：不使用，保留审计
    ARCHIVED = "archived"  # 归档：不再活跃但保留


class Memory(Base, UUIDPrimaryKey, TimestampMixin):
    """记忆条目。

    - 候选记忆必须经用户确认后才能被检索注入上下文。
    - 用户可随时编辑、删除；删除时同时删除向量和原文。
    - 检索限定在 (user_id, character_id) 命名空间内。
    """

    __tablename__ = "memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 记忆内容摘要（用户可读、可编辑）
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 结构化详情（JSON：日期、人物、地点等）
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType, name="memory_type", values_callable=lambda obj: [e.value for e in obj]),
        default=MemoryType.FACT,
        nullable=False,
    )
    status: Mapped[MemoryStatus] = mapped_column(
        Enum(MemoryStatus, name="memory_status", values_callable=lambda obj: [e.value for e in obj]),
        default=MemoryStatus.CANDIDATE,
        nullable=False,
    )

    # 来源消息（候选记忆的提取来源）
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 向量嵌入（用于相似检索）；仅 confirmed 记忆才有有效向量
    embedding: Mapped[object | None] = (
        mapped_column(Vector(EMBEDDING_DIM), nullable=True)
        if _HAS_PGVECTOR
        else mapped_column(Text, nullable=True)  # type: ignore[arg-type]
    )

    # 可用范围（JSON：起始/结束时间、适用场景；空表示全局可用）
    scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 用户确认/编辑审计
    confirmed_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="用户确认时间",
    )

    character: Mapped[Character] = relationship("Character", back_populates="memories")
