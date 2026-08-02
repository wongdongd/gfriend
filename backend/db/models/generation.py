"""生成任务模型。

对应实现方案第 7 节：
- 视觉任务由聊天页或角色主页发起；用户只提交模板选择与短描述。
- 任务通过数据库事务冻结积分，成功确认，失败/取消追加补偿流水。
- 利用 Outbox 防止账务与队列不一致。
- 模型适配器统一提供 submit / getStatus / cancel / normalizeResult / estimateCost。
- 任务、积分、支付与审核操作须具备审计日志；生成任务可重试且保证扣费幂等。
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKey
from db.models.conversation import SafetyStatus

if TYPE_CHECKING:
    from db.models.character import Character
    from db.models.user import User


class TaskType(str, enum.Enum):
    """生成任务类型。"""

    IMAGE = "image"
    VIDEO = "video"


class TaskStatus(str, enum.Enum):
    """生成任务状态。"""

    PENDING = "pending"  # 排队中（已冻结积分，待投递队列）
    QUEUED = "queued"  # 已投递队列
    RUNNING = "running"  # Worker 处理中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败（将退回积分）
    CANCELLED = "cancelled"  # 用户取消（将退回积分）
    SAFETY_BLOCKED = "safety_blocked"  # 审核拦截（将退回积分）


class GenerationTask(Base, UUIDPrimaryKey, TimestampMixin):
    """视觉生成任务。

    积分流向：提交时冻结 → 成功时确认 / 失败时补偿，保证扣费幂等。
    """

    __tablename__ = "generation_tasks"

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
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )

    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", values_callable=lambda obj: [e.value for e in obj]),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    # 优先级（数值越大越优先；按套餐权益）
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ===== 输入快照（JSON：角色视觉设定 + 场景/风格模板 + 情境） =====
    input_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    # 组装后的提示词（审计用）
    assembled_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ===== 供应商信息 =====
    provider: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    provider_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # ===== 积分 =====
    credits_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 关联的积分冻结流水 ID（幂等键）
    freeze_ledger_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("credit_ledger.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 幂等键：同任务的重试不会重复扣费
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)

    # ===== 结果 =====
    result_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ===== 错误与重试 =====
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # 审核状态
    safety_status: Mapped[SafetyStatus] = mapped_column(
        Enum(SafetyStatus, name="safety_status", values_callable=lambda obj: [e.value for e in obj]),
        default=SafetyStatus.PENDING,
        nullable=False,
    )

    # 时间戳
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    character: Mapped["Character"] = relationship("Character", back_populates="generation_tasks")

    __table_args__ = (
        # Worker 按状态 + 优先级拉取待处理任务
        Index("ix_gen_tasks_status_priority", "status", "priority"),
    )


class OutboxEvent(Base, UUIDPrimaryKey, TimestampMixin):
    """Outbox 模式：保证数据库事务与队列投递的一致性。

    API 在冻结积分的同一事务中写入 Outbox 事件；后台轮询/监听将事件可靠投递到 Celery。
    """

    __tablename__ = "outbox_events"

    # 事件类型（如 "generation.submit"、"billing.refund"）
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # 关联的聚合 ID（如 generation_task_id）
    aggregate_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    # 负载（JSON）
    payload: Mapped[str] = mapped_column(Text, nullable=False)

    # 投递状态
    is_published: Mapped[bool] = mapped_column(default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        # Outbox 扫描器按 (is_published, created_at) 拉取未投递事件
        Index("ix_outbox_pending", "is_published", "created_at"),
    )
