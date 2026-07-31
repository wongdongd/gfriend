"""生成任务：图片与视频异步生成。

对应实现方案第 7 节流程：
1. Worker 获取任务
2. 提交模型请求 / 轮询结果
3. 保存作品，确认扣费
4. 失败/取消追加补偿流水
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from worker.celery_app import app

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    """在同步 Celery 任务中运行异步函数。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="worker.tasks.generation.generate_image", bind=True, max_retries=3)
def generate_image(self, task_id: str) -> dict:
    """图片生成任务。"""
    logger.info("开始图片生成任务: %s", task_id)
    return _run_async(_generate(task_id, kind="image"))


@app.task(name="worker.tasks.generation.generate_video", bind=True, max_retries=2)
def generate_video(self, task_id: str) -> dict:
    """视频生成任务（低并发，按套餐优先级）。"""
    logger.info("开始视频生成任务: %s", task_id)
    return _run_async(_generate(task_id, kind="video"))


async def _generate(task_id: str, kind: str) -> dict:
    """实际生成逻辑。"""
    import uuid

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from db.models.billing import CreditEntryType, CreditLedger
    from db.models.generation import GenerationTask, TaskStatus, TaskType
    from db.models.user import User
    from provider_adapters.vision import get_image_adapter, get_video_adapter
    from provider_adapters.vision.base import TaskKind, VisionRequest
    from shared.database import async_session_factory

    async with async_session_factory() as db:  # type: AsyncSession
        # 加载任务
        result = await db.execute(select(GenerationTask).where(GenerationTask.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()
        if not task:
            return {"status": "not_found"}

        if task.status == TaskStatus.CANCELLED:
            return {"status": "cancelled"}

        try:
            task.status = TaskStatus.RUNNING
            await db.commit()

            # 解析输入快照
            snapshot = json.loads(task.input_snapshot)
            prompt_parts = []
            if snapshot.get("character_visual_prompt"):
                prompt_parts.append(snapshot["character_visual_prompt"])
            if snapshot.get("style_template_code"):
                prompt_parts.append(snapshot["style_template_code"])
            if snapshot.get("caption"):
                prompt_parts.append(snapshot["caption"])
            prompt = ", ".join(prompt_parts)

            # 选择适配器
            adapter = get_image_adapter() if kind == "image" else get_video_adapter()
            request = VisionRequest(
                prompt=prompt,
                kind=TaskKind.IMAGE if kind == "image" else TaskKind.VIDEO,
                character_visual_prompt=snapshot.get("character_visual_prompt", ""),
            )

            # 提交并轮询
            provider_task_id = await adapter.submit(request)
            task.provider_task_id = provider_task_id
            task.provider = adapter.provider_name
            await db.commit()

            # 轮询结果（简化：最多等待 60 秒）
            import time
            for _ in range(30):
                result = await adapter.get_status(provider_task_id)
                if result.status.value == "success":
                    break
                if result.status.value == "failed":
                    raise Exception(result.error or "生成失败")
                time.sleep(2)

            if result.status.value != "success":
                raise Exception("生成超时")

            # 保存作品素材
            from db.models.asset import Asset, AssetSource, AssetType
            from db.models.conversation import SafetyStatus

            asset = Asset(
                owner_id=task.user_id,
                character_id=task.character_id,
                type=AssetType.GENERATED_IMAGE if kind == "image" else AssetType.GENERATED_VIDEO,
                source=AssetSource.GENERATION,
                object_key=result.object_key or "",
                mime_type=result.mime_type,
                width=result.width,
                height=result.height,
                duration_seconds=result.duration_seconds,
                generation_task_id=task.id,
                safety_status=SafetyStatus.PENDING,
            )
            db.add(asset)

            # 创建 Work（时间线展示）
            from db.models.asset import Work

            work = Work(
                character_id=task.character_id,
                user_id=task.user_id,
                generation_task_id=task.id,
                primary_asset_id=asset.id,
                scene_template_code=snapshot.get("scene_template_code"),
                style_template_code=snapshot.get("style_template_code"),
                caption=snapshot.get("caption"),
            )
            db.add(work)

            # 确认扣费
            task.status = TaskStatus.SUCCESS
            task.result_asset_id = asset.id
            ledger = CreditLedger(
                user_id=task.user_id,
                type=CreditEntryType.CONSUME,
                amount=-task.credits_cost,
                balance_after=0,  # 实际应查询用户当前余额
                related_task_id=task.id,
                idempotency_key=f"consume:{task.id}",
            )
            db.add(ledger)
            await db.commit()

            return {"status": "success", "asset_id": str(asset.id)}

        except Exception as e:
            logger.exception("生成任务失败: %s", task_id)
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            # 退回积分
            user_result = await db.execute(select(User).where(User.id == task.user_id))
            u = user_result.scalar_one_or_none()
            if u:
                u.credits_balance += task.credits_cost
                refund = CreditLedger(
                    user_id=task.user_id,
                    type=CreditEntryType.REFUND,
                    amount=task.credits_cost,
                    balance_after=u.credits_balance,
                    related_task_id=task.id,
                    idempotency_key=f"refund:{task.id}",
                )
                db.add(refund)
            await db.commit()
            return {"status": "failed", "error": str(e)}
