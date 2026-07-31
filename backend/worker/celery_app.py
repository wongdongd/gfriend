"""Celery 应用配置。

对应实现方案第 7 节：
- 图片、视频使用独立队列；视频队列低并发且按套餐优先级排序。
- Worker 消费 generation 队列，调用 provider_adapters，处理积分确认/补偿。
- 利用 Outbox 防止账务与队列不一致。
"""
from __future__ import annotations

from celery import Celery

from shared.config import settings

app = Celery(
    "companion",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

app.conf.update(
    # 序列化
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # 时区
    timezone="UTC",
    enable_utc=True,
    # 重试
    task_acks_late=True,  # Worker 崩溃时任务重新投递
    task_reject_on_worker_lost=True,
    # 预取
    worker_prefetch_multiplier=1,  # 长任务场景下避免预取过多
    # 队列路由
    task_routes={
        "worker.tasks.generation.generate_image": {"queue": "image"},
        "worker.tasks.generation.generate_video": {"queue": "video"},
        "worker.tasks.safety.moderate_text": {"queue": "safety"},
        "worker.tasks.safety.moderate_image": {"queue": "safety"},
    },
)

# 自动发现任务（worker.tasks 包下的 task 模块）
app.autodiscover_tasks(["worker"], "tasks")

# 显式导入确保任务注册（autodiscover 在某些启动方式下不会立即触发）
try:
    from worker.tasks import generation, outbox, safety  # noqa: F401, E402
except ImportError:
    pass
