"""Celery 应用配置。

对应实现方案第 7 节：
- 图片、视频使用独立队列；视频队列低并发且按套餐优先级排序。
- Worker 消费 generation 队列，调用 provider_adapters，处理积分确认/补偿。
- 利用 Outbox 防止账务与队列不一致。
"""
from __future__ import annotations

import logging
import re
from contextlib import suppress

from celery import Celery
from shared.config import settings

app = Celery(
    "companion",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)

app.conf.update(
    # 日志：不劫持 root logger——保留 shared.logging_config 配置的文件+控制台 handler，
    # 否则 Celery 启动时会移除 root handlers，导致 worker.log 只写入初始化行
    worker_hijack_root_logger=False,
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
    # Celery Beat：周期性扫描 Outbox，把未发布事件投递到对应队列
    beat_schedule={
        "outbox-pending-every-5s": {
            "task": "worker.tasks.outbox.process_pending",
            "schedule": 5.0,  # 每 5 秒扫描一次
            "args": (100,),   # batch_size
        },
    },
)

# 自动发现任务（worker.tasks 包下的 task 模块）
app.autodiscover_tasks(["worker"], "tasks")

# 显式导入确保任务注册（autodiscover 在某些启动方式下不会立即触发）
with suppress(ImportError):
    from worker.tasks import generation, outbox, safety  # noqa: F401, E402


class _OutboxIdleFilter(logging.Filter):
    """过滤 Outbox 扫描任务（每 5 秒一次）的空转日志。

    - "received" 行不含结果信息，一律丢弃；
    - "succeeded ... {'published': 0}" 空转成功记录丢弃；
    - 真正投递（published > 0）、失败/重试的日志全部保留。
    """

    _TASK = "worker.tasks.outbox.process_pending"
    _IDLE_RE = re.compile(r"'published': 0\s*[,}]")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if self._TASK not in msg:
            return True
        if msg.endswith("received"):
            return False
        if "succeeded" in msg and self._IDLE_RE.search(msg):
            return False
        return True


for _noisy_logger in ("celery.worker.strategy", "celery.app.trace"):
    logging.getLogger(_noisy_logger).addFilter(_OutboxIdleFilter())
