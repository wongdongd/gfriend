"""记忆路由：查看、确认、编辑、删除角色可使用的记忆。"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.error_codes import AppError, ErrorCode
from db.models.memory import Memory, MemoryStatus, MemoryType
from db.models.user import User
from shared.database import get_db

router = APIRouter()


class MemoryOut(BaseModel):
    id: str
    character_id: str
    content: str
    type: str
    status: str
    created_at: str


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    type: Optional[MemoryType] = None
    status: Optional[MemoryStatus] = None


@router.get("")
async def list_memories(
    character_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[MemoryStatus] = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看记忆（可按角色、状态过滤）。"""
    stmt = select(Memory).where(Memory.user_id == user.id)
    if character_id:
        stmt = stmt.where(Memory.character_id == character_id)
    if status_filter:
        stmt = stmt.where(Memory.status == status_filter)
    stmt = stmt.order_by(Memory.created_at.desc())
    result = await db.execute(stmt)
    return {
        "items": [
            {"id": str(m.id), "character_id": str(m.character_id), "content": m.content, "type": m.type.value, "status": m.status.value, "created_at": m.created_at.isoformat()}
            for m in result.scalars().all()
        ]
    }


@router.patch("/{memory_id}")
async def update_memory(memory_id: uuid.UUID, req: MemoryUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """编辑或确认/拒绝记忆。"""
    result = await db.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == user.id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise AppError(ErrorCode.RESOURCE_MEMORY_NOT_FOUND)
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(memory, field, value)
    await db.commit()
    return {"ok": True, "status": memory.status.value}


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除记忆（同时删除向量和原文）。"""
    result = await db.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == user.id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise AppError(ErrorCode.RESOURCE_MEMORY_NOT_FOUND)
    await db.delete(memory)
    await db.commit()
