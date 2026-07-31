"""角色路由：创建和管理陪伴角色。"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user
from api.core.error_codes import AppError, ErrorCode
from db.models.character import Character, CharacterStatus
from db.models.user import User
from shared.database import get_db

router = APIRouter()


class CharacterCreate(BaseModel):
    name: str = Field(..., max_length=64)
    companion_preference: Optional[str] = None
    relationship_template_code: Optional[str] = None
    personality_template_code: Optional[str] = None
    visual_style_code: Optional[str] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    companion_preference: Optional[str] = None
    relationship_template_code: Optional[str] = None
    personality_template_code: Optional[str] = None
    visual_style_code: Optional[str] = None
    interaction_bounds: Optional[str] = None
    status: Optional[CharacterStatus] = None


class CharacterOut(BaseModel):
    id: str
    name: str
    companion_preference: Optional[str]
    relationship_template_code: Optional[str]
    personality_template_code: Optional[str]
    visual_style_code: Optional[str]
    status: str
    created_at: str

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
    """删除角色（软删除，级联清理记忆、会话和私有媒体）。"""
    result = await db.execute(select(Character).where(Character.id == character_id, Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise AppError(ErrorCode.RESOURCE_CHARACTER_NOT_FOUND)
    character.status = CharacterStatus.DELETED
    await db.commit()


@router.get("/{character_id}/timeline")
async def get_timeline(character_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = Query(50, le=100)):
    """获取角色共同纪念册（作品时间线）。"""
    from db.models.asset import Work

    result = await db.execute(
        select(Work).where(Work.character_id == character_id, Work.user_id == user.id).order_by(Work.created_at.desc()).limit(limit)
    )
    works = result.scalars().all()
    return {"items": [{"id": str(w.id), "caption": w.caption, "scene_template_code": w.scene_template_code, "created_at": w.created_at.isoformat()} for w in works]}
