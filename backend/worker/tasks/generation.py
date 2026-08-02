"""生成任务：图片与视频异步生成。

对应实现方案第 7 节流程：
1. Worker 获取任务
2. 提交模型请求 / 轮询结果
3. 保存作品，确认扣费
4. 失败/取消追加补偿流水
"""
from __future__ import annotations

import json
import logging

from worker.celery_app import app
from shared.async_runner import run_async

logger = logging.getLogger(__name__)


@app.task(name="worker.tasks.generation.generate_image", bind=True, max_retries=3)
def generate_image(self, task_id: str) -> dict:
    """图片生成任务。"""
    logger.info("开始图片生成任务: %s", task_id)
    return run_async(_generate(task_id, kind="image"))


@app.task(name="worker.tasks.generation.generate_video", bind=True, max_retries=2)
def generate_video(self, task_id: str) -> dict:
    """视频生成任务（低并发，按套餐优先级）。"""
    logger.info("开始视频生成任务: %s", task_id)
    return run_async(_generate(task_id, kind="video"))


async def _generate(task_id: str, kind: str) -> dict:
    """实际生成逻辑。

    事务策略：把"加载任务 + 调用模型 + 轮询"与"写回结果"拆成独立事务，
    避免在单个长事务里持有数据库连接/锁跨越 `time.sleep` 轮询等待。
    """
    import uuid

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from db.models.billing import CreditEntryType, CreditLedger
    from db.models.generation import GenerationTask, TaskStatus, TaskType
    from db.models.user import User
    from provider_adapters.vision import get_image_adapter, get_video_adapter
    from provider_adapters.vision.base import TaskKind, VisionRequest
    from shared.database import async_session_factory

    task_uuid = uuid.UUID(task_id)

    # ===== 事务 1：加载任务，标记 RUNNING =====
    async with async_session_factory() as db:  # type: AsyncSession
        result = await db.execute(select(GenerationTask).where(GenerationTask.id == task_uuid))
        task = result.scalar_one_or_none()
        if not task:
            return {"status": "not_found"}
        if task.status == TaskStatus.CANCELLED:
            return {"status": "cancelled"}

        # 快照任务输入（脱离 session 后仍可用）
        task_user_id = task.user_id
        task_character_id = task.character_id
        task_credits_cost = task.credits_cost
        snapshot = json.loads(task.input_snapshot)

        task.status = TaskStatus.RUNNING
        await db.commit()

    # ===== 事务外：调用视觉模型 + 轮询（不持有 DB 连接）=====
    prompt_parts = []
    if snapshot.get("character_visual_prompt"):
        prompt_parts.append(snapshot["character_visual_prompt"])
    if snapshot.get("style_template_code"):
        prompt_parts.append(snapshot["style_template_code"])
    if snapshot.get("caption"):
        prompt_parts.append(snapshot["caption"])
    prompt = ", ".join(prompt_parts)

    adapter = get_image_adapter() if kind == "image" else get_video_adapter()
    request = VisionRequest(
        prompt=prompt,
        kind=TaskKind.IMAGE if kind == "image" else TaskKind.VIDEO,
        character_visual_prompt=snapshot.get("character_visual_prompt", ""),
    )

    try:
        provider_task_id = await adapter.submit(request)

        # 记录 provider 任务 ID（独立短事务）
        async with async_session_factory() as db:  # type: AsyncSession
            r = await db.execute(select(GenerationTask).where(GenerationTask.id == task_uuid))
            t = r.scalar_one()
            t.provider_task_id = provider_task_id
            t.provider = adapter.provider_name
            await db.commit()

        # 轮询结果（简化：最多等待 60 秒）——不持有 DB 连接
        import time
        vision_result = None
        for _ in range(30):
            vision_result = await adapter.get_status(provider_task_id)
            if vision_result.status.value == "success":
                break
            if vision_result.status.value == "failed":
                raise Exception(vision_result.error or "生成失败")
            time.sleep(2)

        if vision_result is None or vision_result.status.value != "success":
            raise Exception("生成超时")

    except Exception as e:
        # ===== 事务：标记 FAILED + 退回积分 =====
        logger.exception("生成任务失败: %s", task_id)
        async with async_session_factory() as db:  # type: AsyncSession
            r = await db.execute(select(GenerationTask).where(GenerationTask.id == task_uuid))
            t = r.scalar_one_or_none()
            if t is not None:
                t.status = TaskStatus.FAILED
                t.error_message = str(e)
            user_result = await db.execute(
                select(User).where(User.id == task_user_id).with_for_update()
            )
            u = user_result.scalar_one_or_none()
            if u:
                u.credits_balance += task_credits_cost
                db.add(CreditLedger(
                    user_id=task_user_id,
                    type=CreditEntryType.REFUND,
                    amount=task_credits_cost,
                    balance_after=u.credits_balance,
                    related_task_id=task_uuid,
                    idempotency_key=f"refund:{task_uuid}",
                ))
            await db.commit()
        return {"status": "failed", "error": str(e)}

    # ===== 事务 2：保存 asset + work + 标记 SUCCESS + 扣费 =====
    from db.models.asset import Asset, AssetSource, AssetType, Work
    from db.models.conversation import SafetyStatus

    async with async_session_factory() as db:  # type: AsyncSession
        # 重新加载 task（确保 attached 到当前 session）
        r = await db.execute(select(GenerationTask).where(GenerationTask.id == task_uuid))
        task = r.scalar_one()

        # 创建 Asset
        asset = Asset(
            owner_id=task_user_id,
            character_id=task_character_id,
            type=AssetType.GENERATED_IMAGE if kind == "image" else AssetType.GENERATED_VIDEO,
            source=AssetSource.GENERATION,
            object_key=vision_result.object_key or "",
            mime_type=vision_result.mime_type,
            width=vision_result.width,
            height=vision_result.height,
            duration_seconds=vision_result.duration_seconds,
            generation_task_id=task_uuid,
            safety_status=SafetyStatus.PENDING,
        )
        db.add(asset)
        await db.flush()  # 生成 asset.id

        # 创建 Work
        db.add(Work(
            character_id=task_character_id,
            user_id=task_user_id,
            generation_task_id=task_uuid,
            primary_asset_id=asset.id,
            scene_template_code=snapshot.get("scene_template_code"),
            style_template_code=snapshot.get("style_template_code"),
            caption=snapshot.get("caption"),
        ))

        # 标记 SUCCESS 并关联 asset
        task.status = TaskStatus.SUCCESS
        task.result_asset_id = asset.id
        logger.info(
            "[诊断] commit 前: task.id=%s asset.id=%s task.result_asset_id=%s (in-memory)",
            task.id, asset.id, task.result_asset_id,
        )

        # 确认扣费（悲观锁读取最新余额）
        user_result = await db.execute(
            select(User).where(User.id == task_user_id).with_for_update()
        )
        u = user_result.scalar_one_or_none()
        balance_after = u.credits_balance if u else 0

        db.add(CreditLedger(
            user_id=task_user_id,
            type=CreditEntryType.CONSUME,
            amount=-task_credits_cost,
            balance_after=balance_after,
            related_task_id=task_uuid,
            idempotency_key=f"consume:{task_uuid}",
        ))

        await db.commit()
        logger.info("[诊断] commit 后: task.result_asset_id=%s (in-memory)", task.result_asset_id)

        # 重新查询验证是否真的写进数据库
        await db.refresh(task)
        logger.info(
            "[诊断] refresh 后: task.result_asset_id=%s task.status=%s (from DB)",
            task.result_asset_id, task.status.value if task.status else None,
        )
        return {"status": "success", "asset_id": str(asset.id)}
