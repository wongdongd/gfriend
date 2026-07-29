"""Dummy 视觉适配器（本地开发用）。"""
from __future__ import annotations

import asyncio
import uuid

from provider_adapters.vision.base import (
    ProviderTaskStatus,
    TaskKind,
    VisionAdapter,
    VisionRequest,
    VisionResult,
)


class DummyVisionAdapter(VisionAdapter):
    """不调用真实模型的占位视觉适配器。"""

    def __init__(self, kind: TaskKind = TaskKind.IMAGE) -> None:
        self._kind = kind
        self._tasks: dict[str, dict] = {}

    @property
    def provider_name(self) -> str:
        return "dummy"

    async def submit(self, request: VisionRequest) -> str:
        task_id = f"dummy-{uuid.uuid4().hex[:12]}"
        self._tasks[task_id] = {"prompt": request.prompt, "ticks": 0}
        return task_id

    async def get_status(self, provider_task_id: str) -> VisionResult:
        task = self._tasks.get(provider_task_id)
        if task is None:
            return VisionResult(status=ProviderTaskStatus.FAILED, error="task not found")
        # 模拟异步：调用 2 次后完成
        task["ticks"] += 1
        await asyncio.sleep(0.01)
        if task["ticks"] < 2:
            return VisionResult(status=ProviderTaskStatus.RUNNING)
        ext = "png" if self._kind == TaskKind.IMAGE else "mp4"
        return VisionResult(
            status=ProviderTaskStatus.SUCCESS,
            object_key=f"generated/{provider_task_id}.{ext}",
            mime_type=f"image/{ext}" if self._kind == TaskKind.IMAGE else f"video/{ext}",
            width=1024,
            height=1024,
            duration_seconds=5.0 if self._kind == TaskKind.VIDEO else None,
            raw={"prompt": task["prompt"]},
        )

    async def cancel(self, provider_task_id: str) -> bool:
        task = self._tasks.pop(provider_task_id, None)
        return task is not None

    def normalize_result(self, raw: dict, kind: TaskKind) -> VisionResult:
        return VisionResult(status=ProviderTaskStatus.SUCCESS, raw=raw)

    def estimate_cost(self, request: VisionRequest) -> int:
        return 10 if request.kind == TaskKind.IMAGE else 50
