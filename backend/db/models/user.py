"""用户与身份认证模型。

对应实现方案：
- ``User`` 以内部 ``id``（UUID）作为全业务主键，绝不以 Google/Facebook 返回的 ID 直接作为主键。
- 每个外部账号映射为一条 ``AuthIdentity``；同一用户可绑定邮箱、Google、Facebook 多种身份。
- 首次创建账户后再执行年龄确认、条款同意与通知授权。
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from db.models.character import Character
    from db.models.billing import CreditLedger, Order, Subscription


class AgeStatus(str, enum.Enum):
    """年龄确认状态。"""

    UNCONFIRMED = "unconfirmed"  # 未确认
    CONFIRMED = "confirmed"  # 已确认成年
    MINOR = "minor"  # 未成年


class UserRole(str, enum.Enum):
    """账户角色。"""

    USER = "user"  # 普通用户
    ADMIN = "admin"  # 管理员
    OPERATOR = "operator"  # 运营


class User(Base, UUIDPrimaryKey, TimestampMixin):
    """用户主表，全业务主键。"""

    __tablename__ = "users"

    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # 邮箱密码登录使用；OAuth 用户为空。仅存 bcrypt 哈希。
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    display_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # 年龄与合规
    age_status: Mapped[AgeStatus] = mapped_column(
        Enum(AgeStatus, name="age_status", values_callable=lambda obj: [e.value for e in obj]),
        default=AgeStatus.UNCONFIRMED,
        nullable=False,
    )
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 角色
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.USER,
        nullable=False,
    )

    # 通知偏好（JSON 字符串：push_frequency, proactive_message_enabled 等）
    notification_prefs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 订阅权益快照（冗余，便于快速读取；以 Subscription 为准）
    subscription_tier: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    credits_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 账户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 关系
    auth_identities: Mapped[list["AuthIdentity"]] = relationship(
        "AuthIdentity", back_populates="user", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        "Character", back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="user")
    credit_ledger: Mapped[list["CreditLedger"]] = relationship("CreditLedger", back_populates="user")


class AuthProvider(str, enum.Enum):
    """身份提供者类型。"""

    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"


class AuthIdentity(Base, UUIDPrimaryKey, TimestampMixin):
    """外部身份与本地用户的绑定关系。

    一个用户可同时绑定邮箱、Google、Facebook，避免误以不同方式登录而出现多个账户。
    """

    __tablename__ = "auth_identities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider, name="auth_provider", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    # 服务商返回的稳定账号 ID（邮箱登录时等于 email）
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # 冗余邮箱，便于已验证邮箱的谨慎自动合并
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 加密存储或不落库（OAuth access/refresh token 等）
    access_token_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="auth_identities")

    __table_args__ = (
        UniqueConstraint("provider", "provider_account_id", name="uq_auth_provider_account"),
        {"comment": "外部身份绑定；一个用户可绑定多个 provider"},
    )
