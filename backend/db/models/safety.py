"""安全事件模型。

对应实现方案第 3 节 safety 模块、第 11 节部署与安全基线：
- 文本/图片审核、风险检测、举报、人工审核队列和策略版本。
- 任务、积分、支付与审核操作须具备审计日志。
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKey


class RiskType(str, enum.Enum):
    """风险类型。"""

    SPAM = "spam"  # 垃圾信息
    HARASSMENT = "harassment"  # 骚扰
    HATE = "hate"  # 仇恨言论
    SEXUAL = "sexual"  # 性化内容
    VIOLENCE = "violence"  # 暴力
    SELF_HARM = "self_harm"  # 自伤
    CRISIS = "crisis"  # 危机（心理风险）
    MINOR_SAFETY = "minor_safety"  # 未成年安全
    COPYRIGHT = "copyright"  # 肖像权/版权
    OTHER = "other"


class DispositionStatus(str, enum.Enum):
    """处置状态。"""

    PENDING = "pending"  # 待处理
    REVIEWING = "reviewing"  # 人工审核中
    RESOLVED = "resolved"  # 已解决（放行）
    ACTIONED = "actioned"  # 已处置（拦截/封禁）
    ESCALATED = "escalated"  # 已升级


class SafetyEvent(Base, UUIDPrimaryKey, TimestampMixin):
    """安全事件：覆盖文本、图片、视频、用户行为等多维度。

    审计信息包括触发来源、策略版本、处置操作与操作人。
    """

    __tablename__ = "safety_events"

    # 关联实体（任一）
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    generation_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    risk_type: Mapped[RiskType] = mapped_column(
        Enum(RiskType, name="risk_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    # 风险等级（low / medium / high / critical）
    severity: Mapped[str] = mapped_column(String(16), default="low", nullable=False)

    # 触发来源（auto / report）
    source: Mapped[str] = mapped_column(String(16), default="auto", nullable=False)
    # 举报人（source=report 时有效）
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 策略版本
    policy_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # 事件详情（JSON：模型返回的原始结果、命中的规则等）
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 处置
    disposition: Mapped[DispositionStatus] = mapped_column(
        Enum(DispositionStatus, name="disposition_status", values_callable=lambda obj: [e.value for e in obj]),
        default=DispositionStatus.PENDING,
        nullable=False,
    )
    # 处置动作（JSON：block_message / freeze_user / refund_credits 等）
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    handled_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
