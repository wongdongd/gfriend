"""角色路由：创建和管理陪伴角色。"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from db.models.character import Character, CharacterStatus
from db.models.user import User
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from shared.database import get_db
from sqlalchemy import delete as sql_delete
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user
from api.core.error_codes import AppError, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter()


class CharacterCreate(BaseModel):
    name: str = Field(..., max_length=64)
    companion_preference: str | None = None
    relationship_template_code: str | None = None
    personality_template_code: str | None = None
    visual_style_code: str | None = None


class CharacterUpdate(BaseModel):
    name: str | None = None
    companion_preference: str | None = None
    relationship_template_code: str | None = None
    personality_template_code: str | None = None
    visual_style_code: str | None = None
    interaction_bounds: str | None = None
    status: CharacterStatus | None = None


class CharacterOut(BaseModel):
    id: uuid.UUID
    name: str
    companion_preference: str | None
    relationship_template_code: str | None
    personality_template_code: str | None
    visual_style_code: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[CharacterOut])
async def list_characters(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户的角色列表。"""
    result = await db.execute(
        select(Character).where(Character.user_id == user.id, Character.status != CharacterStatus.DELETED).order_by(Character.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=CharacterOut, status_code=status.HTTP_201_CREATED)
async def create_character(req: CharacterCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建陪伴角色。"""
    character = Character(
        user_id=user.id,
        name=req.name,
        companion_preference=req.companion_preference,
        relationship_template_code=req.relationship_template_code,
        personality_template_code=req.personality_template_code,
        visual_style_code=req.visual_style_code,
        status=CharacterStatus.ACTIVE,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@router.get("/{character_id}", response_model=CharacterOut)
async def get_character(character_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取角色详情。"""
    result = await db.execute(select(Character).where(Character.id == character_id, Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character or character.status == CharacterStatus.DELETED:
        raise AppError(ErrorCode.RESOURCE_CHARACTER_NOT_FOUND)
    return character


@router.patch("/{character_id}", response_model=CharacterOut)
async def update_character(character_id: uuid.UUID, req: CharacterUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新角色。"""
    result = await db.execute(select(Character).where(Character.id == character_id, Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise AppError(ErrorCode.RESOURCE_CHARACTER_NOT_FOUND)
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(character, field, value)
    await db.commit()
    await db.refresh(character)
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(character_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除角色（软删除，级联清理记忆、会话和私有媒体）。

    对已删除的角色重复调用返回 404，便于区分"真删除"与"重复删除"。
    """
    from db.models.asset import Asset, Work
    from db.models.conversation import Conversation, Message
    from db.models.memory import Memory

    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == user.id,
            Character.status != CharacterStatus.DELETED,
        )
    )
    character = result.scalar_one_or_none()
    if not character:
        raise AppError(ErrorCode.RESOURCE_CHARACTER_NOT_FOUND)
    character.status = CharacterStatus.DELETED

    # 级联清理：记忆（含向量）→ 消息 → 会话 → 作品时间线
    await db.execute(sql_delete(Memory).where(Memory.character_id == character_id))
    await db.execute(
        sql_delete(Message).where(
            Message.conversation_id.in_(select(Conversation.id).where(Conversation.character_id == character_id))
        )
    )
    await db.execute(sql_delete(Conversation).where(Conversation.character_id == character_id))
    await db.execute(sql_delete(Work).where(Work.character_id == character_id))

    # 私有媒体：软删除素材记录（含角色参考图）
    asset_conditions = [Asset.character_id == character_id]
    if character.reference_asset_id:
        asset_conditions.append(Asset.id == character.reference_asset_id)
    assets_result = await db.execute(select(Asset).where(or_(*asset_conditions), Asset.is_deleted == False))  # noqa: E712
    assets = assets_result.scalars().all()
    for asset in assets:
        asset.soft_delete()

    await db.commit()

    # 对象存储中的媒体文件做最大努力清理（失败仅记录日志，不影响删除结果）
    if assets:
        from provider_adapters.storage import get_storage

        storage = get_storage()
        for asset in assets:
            try:
                await storage.delete(asset.object_key)
            except Exception:
                logger.warning("清理对象存储失败 object_key=%s", asset.object_key, exc_info=True)


@router.get("/{character_id}/timeline")
async def get_timeline(character_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = Query(50, le=100)):
    """获取角色共同纪念册（作品时间线）。"""
    from db.models.asset import Work

    result = await db.execute(
        select(Work).where(Work.character_id == character_id, Work.user_id == user.id).order_by(Work.created_at.desc()).limit(limit)
    )
    works = result.scalars().all()
    return {"items": [{"id": str(w.id), "caption": w.caption, "scene_template_code": w.scene_template_code, "created_at": w.created_at.isoformat()} for w in works]}
