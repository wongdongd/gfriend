"""会话与消息模型。

对应实现方案第 4 节、第 6 节：
- 对话请求应同步快速返回；角色回复以 SSE/WebSocket 流式呈现。
- ``Message`` 须保存模型/模板/策略快照。
- 输出安全检查在保存前执行。
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from db.models.character import Character


class MessageRole(str, enum.Enum):
    """消息发送方。"""

    USER = "user"  # 用户消息
    ASSISTANT = "assistant"  # 角色消息
    SYSTEM = "system"  # 系统提示（不展示给用户）


class MessageFeedback(str, enum.Enum):
    """用户对角色回复的反馈。"""

    NONE = "none"
    LIKE = "like"
    DISLIKE = "dislike"
    ADJUST_TONE = "adjust_tone"  # 调整语气


class SafetyStatus(str, enum.Enum):
    """内容安全状态。"""

    PENDING = "pending"  # 待审核
    PASS = "pass"  # 通过
    FLAGGED = "flagged"  # 标记
    BLOCKED = "blocked"  # 拦截
    REVIEWING = "reviewing"  # 人工审核中


class Conversation(Base, UUIDPrimaryKey, TimestampMixin):
    """会话：用户与某角色的一段持续对话。"""

    __tablename__ = "conversations"

    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    # 快捷话题标记（JSON 数组：早安、分享今天、倾诉烦恼...）
    quick_topics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    character: Mapped["Character"] = relationship("Character", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # 按角色 + 最后消息时间倒序查询最近会话
        Index("ix_conversations_char_lastmsg", "character_id", "last_message_at"),
    )


class Message(Base, UUIDPrimaryKey, TimestampMixin):
    """单条消息。保存模型/模板/策略快照以便审计与回放。"""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 附件（图片/视频 URL 列表，JSON 存储）
    attachments: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # ===== 快照字段（用于审计与成本追踪） =====
    model_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    template_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    policy_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # 用户反馈
    feedback: Mapped[MessageFeedback] = mapped_column(
        Enum(MessageFeedback, name="message_feedback", values_callable=lambda obj: [e.value for e in obj]),
        default=MessageFeedback.NONE,
        nullable=False,
    )
    feedback_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 安全状态
    safety_status: Mapped[SafetyStatus] = mapped_column(
        Enum(SafetyStatus, name="safety_status", values_callable=lambda obj: [e.value for e in obj]),
        default=SafetyStatus.PENDING,
        nullable=False,
    )

    # 关联的生成任务（如本消息触发了图片生成）
    generation_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # token 计数（成本追踪）
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        # 按会话 + 创建时间倒序查询消息历史（最常用查询模式）
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )
