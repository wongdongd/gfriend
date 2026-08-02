"""计费模型：积分流水、订单、订阅。

对应实现方案第 8 节：
- 支付不直接处理或保存银行卡信息；后端创建第三方支付服务商提供的结账会话。
- 订阅的创建、续费、取消、扣款失败和退款均以服务商签名 Webhook 为准。
- 支付 Webhook 必须验证签名、记录事件 ID 并按事件 ID 幂等处理。
- 图片和视频消耗仍由内部 ``CreditLedger`` 和任务结算处理。
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from db.models.user import User


class CreditEntryType(str, enum.Enum):
    """积分流水类型。"""

    GRANT = "grant"  # 赠送/试用
    PURCHASE = "purchase"  # 购买积分包
    SUBSCRIPTION = "subscription"  # 订阅附赠
    FREEZE = "freeze"  # 冻结（提交生成任务）
    CONSUME = "consume"  # 确认消耗（任务成功）
    REFUND = "refund"  # 退回（任务失败/取消）
    ADJUST = "adjust"  # 人工调整


class CreditLedger(Base, UUIDPrimaryKey, TimestampMixin):
    """积分流水账本。

    每条记录代表一次余额变动；``balance_after`` 为快照，便于审计。
    冻结 → 确认/退回 的闭环通过 ``related_task_id`` 与 ``idempotency_key`` 保证幂等。
    """

    __tablename__ = "credit_ledger"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[CreditEntryType] = mapped_column(
        Enum(CreditEntryType, name="credit_entry_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    # 金额（正数为入账，负数为出账）
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    # 余额快照
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)

    # 关联实体
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 幂等键
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="credit_ledger")

    __table_args__ = (
        # 用户积分流水查询（最常用：按用户 + 时间倒序）
        Index("ix_credit_ledger_user_created", "user_id", "created_at"),
    )


class OrderType(str, enum.Enum):
    """订单类型。"""

    SUBSCRIPTION = "subscription"  # 订阅套餐
    CREDITS = "credits"  # 积分包


class OrderStatus(str, enum.Enum):
    """订单状态。"""

    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    FAILED = "failed"  # 支付失败
    REFUNDED = "refunded"  # 已退款
    CANCELLED = "cancelled"  # 已取消


class PaymentChannel(str, enum.Enum):
    """支付渠道。"""

    STRIPE = "stripe"
    WECHAT = "wechat"
    ALIPAY = "alipay"


class Order(Base, UUIDPrimaryKey, TimestampMixin):
    """订单。支付状态以 Webhook 为准，浏览器跳转仅用于展示。"""

    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="order_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", values_callable=lambda obj: [e.value for e in obj]),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    # 金额（最小货币单位，如分）
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="usd", nullable=False)

    # 套餐/积分包标识
    sku_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # 积分包数量（type=credits 时有效）
    credits_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 支付渠道
    channel: Mapped[PaymentChannel] = mapped_column(
        Enum(PaymentChannel, name="payment_channel", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    # 第三方会话/支付意图 ID
    provider_checkout_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Webhook 事件 ID（幂等）
    provider_event_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="orders")


class SubscriptionStatus(str, enum.Enum):
    """订阅状态。"""

    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"  # 扣款失败宽限期
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Subscription(Base, UUIDPrimaryKey, TimestampMixin):
    """用户订阅。状态以服务商 Webhook 为准。"""

    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status", values_callable=lambda obj: [e.value for e in obj]),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )

    # 套餐标识（free / companion / pro）
    tier: Mapped[str] = mapped_column(String(32), nullable=False)
    # 权益快照（JSON：角色数上限、对话额度、记忆容量、图片额度等）
    entitlements: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 周期
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False, nullable=False)

    # 渠道
    channel: Mapped[PaymentChannel] = mapped_column(
        Enum(PaymentChannel, name="payment_channel", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="subscriptions")

    __table_args__ = (
        UniqueConstraint("user_id", "channel", name="uq_subscription_user_channel"),
    )
