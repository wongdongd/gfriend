"""角色（陪伴人物）模型。

对应实现方案第 4 节：``Character`` 实体。
角色档案 = 关系模板 + 人格模板 + 视觉设定 + 陪伴偏好 + 状态。
专业提示词不直接暴露给用户；此处存储的是组合后的角色档案。
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from db.models.user import User
    from db.models.conversation import Conversation
    from db.models.memory import Memory
    from db.models.asset import Asset
    from db.models.generation import GenerationTask


class CharacterStatus(str, enum.Enum):
    """角色状态。"""

    ACTIVE = "active"  # 正常使用
    PAUSED = "paused"  # 用户主动暂停（静音/暂停主动消息）
    ARCHIVED = "archived"  # 归档（不删除但不可用）
    DELETED = "deleted"  # 软删除


class Character(Base, UUIDPrimaryKey, TimestampMixin):
    """陪伴人物角色。

    所有创作能力均围绕"我的人物"展开。一个用户在订阅权益内可拥有多个角色。
    """

    __tablename__ = "characters"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 用户填写的"希望 TA 怎样陪伴我"
    companion_preference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ===== 模板引用（code 字符串，避免硬绑定模板行） =====
    relationship_template_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    personality_template_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # ===== 角色档案快照（JSON 字符串） =====
    # 人格提示词（组装后，不直接暴露给用户）
    persona_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 关系设定（边界、互动方式）
    relationship_setting: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 视觉提示词（外观描述，用于图片/视频生成）
    visual_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 视觉风格模板 code
    visual_style_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # 角色参考图 asset_id（用户上传，需拥有使用权）
    reference_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 互动边界（JSON：允许/禁止的话题、主动消息频率等）
    interaction_bounds: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 模型参数快照（温度、top_p 等；JSON）
    model_params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 状态
    status: Mapped[CharacterStatus] = mapped_column(
        Enum(CharacterStatus, name="character_status", values_callable=lambda obj: [e.value for e in obj]),
        default=CharacterStatus.ACTIVE,
        nullable=False,
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="characters")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="character", cascade="all, delete-orphan"
    )
    memories: Mapped[list["Memory"]] = relationship(
        "Memory", back_populates="character", cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", back_populates="character", foreign_keys="Asset.character_id"
    )
    generation_tasks: Mapped[list["GenerationTask"]] = relationship(
        "GenerationTask", back_populates="character"
    )
