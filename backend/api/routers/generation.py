"""视觉生成任务路由：创建任务、查询状态。

对应实现方案第 7 节：
- 事务：冻结积分 + 创建任务 + Outbox。
- 用户只提交模板选择与短描述；后端自动组装提示词。
- 任务通过数据库事务冻结积分，成功确认，失败/取消追加补偿流水。
"""
from __future__ import annotations

import json
import uuid

from db.models.character import Character, CharacterStatus
from db.models.generation import GenerationTask, OutboxEvent, TaskStatus, TaskType
from db.models.user import User
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from shared.config import settings
from shared.database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user
from api.core.error_codes import AppError, ErrorCode

router = APIRouter()


class CreateTaskRequest(BaseModel):
    character_id: str
    type: TaskType = TaskType.IMAGE
    scene_template_code: str | None = None
    style_template_code: str | None = None
    caption: str | None = None  # 用户补充的情境描述
    conversation_id: str | None = None


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

    # 估算积分消耗（MVP 固定值；从 settings 读取便于运营调整）
    if req.type == TaskType.IMAGE:
        credits_cost = settings.image_cost_credits
    else:
        credits_cost = settings.video_cost_credits

    # 是否为首张角色形象图：用户尚无任何角色 → 此次生成视为"首次赠送"
    # 此场景下免积分扣减，不校验余额与订阅。其余场景必须校验积分。
    existing_chars_q = await db.execute(
        select(Character.id).where(Character.user_id == user.id, Character.status != CharacterStatus.DELETED).limit(1)
    )
    is_first_portrait = existing_chars_q.first() is None and req.type == TaskType.IMAGE

    if is_first_portrait:
        # 免费首张：不冻结积分，不写 FREEZE 流水；credits_cost 记 0 以便后续审计/取消时正确处理
        credits_cost = 0
        locked_user = None
    else:
        # 悲观锁：SELECT ... FOR UPDATE 防止并发超额消费
        lock_result = await db.execute(
            select(User).where(User.id == user.id).with_for_update()
        )
        locked_user = lock_result.scalar_one()
        if locked_user.credits_balance < credits_cost:
            raise AppError(ErrorCode.BILLING_INSUFFICIENT_CREDITS)
        # 冻结积分（提交事务原子）
        locked_user.credits_balance -= credits_cost

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

    # 创建任务 + Outbox（同一事务）；积分已在上方分支冻结
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
        "credits_balance": locked_user.credits_balance if locked_user is not None else user.credits_balance,
    }


@router.get("/{task_id}")
async def get_task(task_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """查看生成任务状态。成功后返回结果签名访问 URL。"""
    import logging

    from db.models.asset import Asset

    logger = logging.getLogger(__name__)

    result = await db.execute(select(GenerationTask).where(GenerationTask.id == task_id, GenerationTask.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise AppError(ErrorCode.RESOURCE_TASK_NOT_FOUND)

    url: str | None = None
    if task.status == TaskStatus.SUCCESS and task.result_asset_id:
        asset_res = await db.execute(select(Asset).where(Asset.id == task.result_asset_id, Asset.owner_id == user.id))
        asset = asset_res.scalar_one_or_none()
        if asset and asset.object_key:
            from provider_adapters.storage import get_storage

            storage = get_storage()
            try:
                url = await storage.presigned_get_url(asset.object_key, settings.s3_presign_expires)
            except Exception as e:  # noqa: BLE001
                # 对象存储不可达时降级：返回 null url，前端展示"暂时不可用"而非 500
                logger.warning("生成签名 URL 失败 (object_key=%s): %s", asset.object_key, e)
        else:
            logger.warning(
                "任务 %s 标记 SUCCESS 但 asset 缺失或 object_key 为空: result_asset_id=%s",
                task_id,
                task.result_asset_id,
            )
    elif task.status == TaskStatus.SUCCESS:
        logger.warning("任务 %s 标记 SUCCESS 但 result_asset_id 为空", task_id)

    return {
        "id": str(task.id),
        "type": task.type.value,
        "status": task.status.value,
        "url": url,
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
    # 退回积分时使用悲观锁防止并发修改
    lock_result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = lock_result.scalar_one()
    locked_user.credits_balance += task.credits_cost  # 退回积分
    await db.commit()
    return {"ok": True, "credits_balance": locked_user.credits_balance}
