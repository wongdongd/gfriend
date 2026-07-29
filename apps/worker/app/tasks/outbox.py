"""Outbox 事件处理器：将数据库中的 Outbox 事件可靠投递到 Celery 队列。

对应实现方案第 7 节：利用 Outbox 防止账务与队列不一致。
所有队列事件可由数据库 Outbox 恢复。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.celery_app import app

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="app.tasks.outbox.process_pending", bind=True)
def process_pending(self, batch_size: int = 100) -> dict:
    """扫描未发布的 Outbox 事件并投递到 Celery。

    应由定时任务（Celery Beat）周期性调用。
    """
    return _run_async(_process_outbox(batch_size))


async def _process_outbox(batch_size: int) -> dict:
    import uuid

    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession

    from db.models.generation import OutboxEvent
    from shared.database import async_session_factory

    published = 0
    async with async_session_factory() as db:  # type: AsyncSession
        result = await db.execute(
            select(OutboxEvent).where(OutboxEvent.is_published.is_(False)).limit(batch_size)
        )
        events = result.scalars().all()

        for event in events:
            try:
                payload = json.loads(event.payload)
                if event.event_type == "generation.submit":
                    # 投递到对应队列
                    task_type = payload.get("type", "image")
                    from app.tasks.generation import generate_image, generate_video

                    if task_type == "video":
                        generate_video.delay(str(event.aggregate_id))
                    else:
                        generate_image.delay(str(event.aggregate_id))

                # 标记已发布
                event.is_published = True
                from datetime import datetime, timezone

                event.published_at = datetime.now(timezone.utc)
                published += 1
            except Exception:
                logger.exception("Outbox 事件投递失败: %s", event.id)
                event.retry_count += 1

        await db.commit()

    return {"published": published}
