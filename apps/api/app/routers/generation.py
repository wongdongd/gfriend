"""视觉生成任务路由：创建任务、查询状态。

对应实现方案第 7 节：
- 事务：冻结积分 + 创建任务 + Outbox。
- 用户只提交模板选择与短描述；后端自动组装提示词。
- 任务通过数据库事务冻结积分，成功确认，失败/取消追加补偿流水。
"""
from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.error_codes import AppError, ErrorCode
from db.models.character import Character, CharacterStatus
from db.models.generation import GenerationTask, OutboxEvent, TaskStatus, TaskType
from db.models.user import User
from shared.database import get_db

router = APIRouter()


class CreateTaskRequest(BaseModel):
    character_id: str
    type: TaskType = TaskType.IMAGE
    scene_template_code: Optional[str] = None
    style_template_code: Optional[str] = None
    caption: Optional[str] = None  # 用户补充的情境描述
    conversation_id: Optional[str] = None


@router.post("")
async def create_task(req: CreateTaskRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """提交角色视觉内容任务。

    事务：校验权益 → 组装参数快照 → 冻结积分 → 创建任务 + Outbox → 返回排队中。
    实际生成由 Celery Worker 异步处理。
    """
    # 校验角色
    result = await db.execute(select(Character).where(Character.id == uuid.UUID(req.character_id), Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character or character.status == CharacterStatus.DELETED:
        raise AppError(ErrorCode.RESOURCE_CHARACTER_NOT_FOUND)

    # 估算积分消耗（MVP 固定值）
    credits_cost = 10 if req.type == TaskType.IMAGE else 50
    if user.credits_balance < credits_cost:
        raise AppError(ErrorCode.BILLING_INSUFFICIENT_CREDITS)

    # 组装输入快照
    input_snapshot = json.dumps({
        "character_id": str(character.id),
        "character_visual_prompt": character.visual_prompt or "",
        "scene_template_code": req.scene_template_code,
        "style_template_code": req.style_template_code,
        "caption": req.caption or "",
    }, ensure_ascii=False)

    # 幂等键
    idem_key = f"gen:{user.id}:{uuid.uuid4().hex}"

    # 冻结积分 + 创建任务 + Outbox（同一事务）
    user.credits_balance -= credits_cost
    task = GenerationTask(
        user_id=user.id,
        character_id=character.id,
        conversation_id=uuid.UUID(req.conversation_id) if req.conversation_id else None,
        type=req.type,
        status=TaskStatus.PENDING,
        input_snapshot=input_snapshot,
        credits_cost=credits_cost,
        idempotency_key=idem_key,
    )
    db.add(task)
    await db.flush()

    # Outbox 事件（保证数据库事务与队列投递一致性）
    outbox = OutboxEvent(
        event_type="generation.submit",
        aggregate_id=task.id,
        payload=json.dumps({"task_id": str(task.id), "type": req.type.value}, ensure_ascii=False),
    )
    db.add(outbox)
    await db.commit()

    return {
        "task_id": str(task.id),
        "status": task.status.value,
        "credits_cost": credits_cost,
        "credits_balance": user.credits_balance,
    }


@router.get("/{task_id}")
async def get_task(task_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """查看生成任务状态。"""
    result = await db.execute(select(GenerationTask).where(GenerationTask.id == task_id, GenerationTask.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise AppError(ErrorCode.RESOURCE_TASK_NOT_FOUND)
    return {
        "id": str(task.id),
        "type": task.type.value,
        "status": task.status.value,
        "credits_cost": task.credits_cost,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """取消生成任务（退回积分）。"""
    result = await db.execute(select(GenerationTask).where(GenerationTask.id == task_id, GenerationTask.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise AppError(ErrorCode.RESOURCE_TASK_NOT_FOUND)
    if task.status not in (TaskStatus.PENDING, TaskStatus.QUEUED):
        raise AppError(ErrorCode.TASK_CANNOT_CANCEL)
    task.status = TaskStatus.CANCELLED
    user.credits_balance += task.credits_cost  # 退回积分
    await db.commit()
    return {"ok": True, "credits_balance": user.credits_balance}
