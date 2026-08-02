"""模板模型。

对应实现方案第 4 节：``Template`` 实体，类型涵盖关系/人格/场景/风格。
模板包含展示配置与提示词片段，由管理后台维护并支持版本与发布状态。
"""
from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import JSON, Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKey


class TemplateType(str, enum.Enum):
    """模板类型。"""

    RELATIONSHIP = "relationship"  # 关系模板：朋友、恋人、治愈伙伴...
    PERSONALITY = "personality"  # 人格原型：温柔可靠、活泼元气...
    SCENE = "scene"  # 视觉场景：日常自拍、一起旅行、节日问候...
    STYLE = "style"  # 视觉风格：写实电影感、清新生活、日系插画...


class Template(Base, UUIDPrimaryKey, TimestampMixin):
    """关系 / 人格 / 场景 / 风格模板。

    - ``display_config``：前端展示配置（JSON：名称、描述、图标、预览图等）。
    - ``prompt_snippet``：注入到 LLM 或视觉模型提示词的片段。
    - ``policy_version``：策略版本，便于审计与回滚。
    """

    __tablename__ = "templates"

    type: Mapped[TemplateType] = mapped_column(
        Enum(TemplateType, name="template_type", values_callable=lambda obj: [e.value for e in obj]),
        index=True,
        nullable=False,
    )
    # 模板唯一标识（如 "relationship.friend"、"style.cinematic"）
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    display_config: Mapped[dict] = mapped_column(JSON, nullable=False, comment="名称/描述/图标/预览图")
    prompt_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 视觉缩略图 URL（场景/风格模板用）
    preview_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    policy_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
