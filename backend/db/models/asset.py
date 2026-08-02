"""素材与作品模型。

对应实现方案第 4 节、第 7 节：
- ``Asset``：角色参考图、生成作品、缩略图、导出文件。
- 所有媒体通过短期签名 URL 访问；默认私有。
- 图片/视频必须经审核并存入私有对象存储后才能呈现给用户。
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey
from db.models.conversation import SafetyStatus

if TYPE_CHECKING:
    from db.models.character import Character


class AssetType(str, enum.Enum):
    """媒体类型。"""

    REFERENCE_IMAGE = "reference_image"  # 角色参考图（用户上传）
    GENERATED_IMAGE = "generated_image"  # 生成的图片
    GENERATED_VIDEO = "generated_video"  # 生成的视频
    THUMBNAIL = "thumbnail"  # 缩略图
    EXPORT = "export"  # 数据导出文件


class AssetSource(str, enum.Enum):
    """素材来源。"""

    USER_UPLOAD = "user_upload"
    GENERATION = "generation"
    SYSTEM = "system"


class Asset(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """媒体素材/作品。存储于 S3 兼容对象存储，通过签名 URL 访问。

    - ``object_key``：对象存储键（不保存完整 URL，签名 URL 临时生成）。
    - ``access_policy``：访问策略（private / signed）。
    - 审核未通过的内容不对外呈现。
    """

    __tablename__ = "assets"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    source: Mapped[AssetSource] = mapped_column(
        Enum(AssetSource, name="asset_source", values_callable=lambda obj: [e.value for e in obj]),
        default=AssetSource.USER_UPLOAD,
        nullable=False,
    )

    # 对象存储
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    bucket: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 图片/视频尺寸
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True, comment="视频时长(秒)")

    # 访问策略
    access_policy: Mapped[str] = mapped_column(String(32), default="signed", nullable=False)

    # 审核状态（复用 SafetyStatus）
    safety_status: Mapped[SafetyStatus] = mapped_column(
        Enum(SafetyStatus, name="safety_status", values_callable=lambda obj: [e.value for e in obj]),
        default=SafetyStatus.PENDING,
        nullable=False,
    )

    # 关联的生成任务（如本素材由某任务生成）
    generation_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 元数据（JSON：如生成参数、模型版本等）
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    character: Mapped[Character | None] = relationship(
        "Character", back_populates="assets", foreign_keys="Asset.character_id"
    )


class Work(Base, UUIDPrimaryKey, TimestampMixin):
    """作品：在角色主页时间线展示的视觉内容单元。

    一个 Work 可包含多个 Asset（如图片+缩略图，或视频+封面）。
    """

    __tablename__ = "works"

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

    # 源任务
    generation_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 主素材
    primary_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 场景模板 code + 风格模板 code（时间线展示用）
    scene_template_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    style_template_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 用户补充的情境描述
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间线展示信息
    display_at: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="展示时间标签")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
