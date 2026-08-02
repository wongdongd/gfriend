"""Dummy 视觉适配器（本地开发用）。

成功时会生成一张纯色占位 PNG 并上传到对象存储（MinIO），
让前端能真正拿到图片 URL 并展示，无需依赖真实图像模型。
"""
from __future__ import annotations

import asyncio
import io
import struct
import uuid
import zlib

from provider_adapters.vision.base import (
    ProviderTaskStatus,
    TaskKind,
    VisionAdapter,
    VisionRequest,
    VisionResult,
)


def _make_png(width: int, height: int, prompt: str) -> bytes:
    """用纯标准库生成一张渐变 PNG（无第三方依赖）。

    颜色基于 prompt 哈希，让不同 prompt 生成不同色调，便于区分。
    """
    seed = abs(hash(prompt)) % 360
    # HSL → RGB 简化：取三个色相点做渐变
    def hsl_to_rgb(h: int, s: float, l: float) -> tuple[int, int, int]:
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

    top = hsl_to_rgb(seed, 0.6, 0.45)
    bottom = hsl_to_rgb((seed + 80) % 360, 0.6, 0.25)

    # 构造逐行渐变的 RGB 像素
    raw = bytearray()
    for y in range(height):
        ratio = y / max(height - 1, 1)
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        raw.append(0)  # PNG 行过滤类型 0（None）
        for _ in range(width):
            raw.extend((r, g, b))

    def _chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit, color type 2 (RGB)
    idat = zlib.compress(bytes(raw), 9)
    iend = b""
    return sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", iend)


class DummyVisionAdapter(VisionAdapter):
    """不调用真实模型的占位视觉适配器。

    成功时生成纯色 PNG 并上传到对象存储，让本地开发链路完整可展示。
    """

    def __init__(self, kind: TaskKind = TaskKind.IMAGE) -> None:
        self._kind = kind
        self._tasks: dict[str, dict] = {}

    @property
    def provider_name(self) -> str:
        return "dummy"

    async def submit(self, request: VisionRequest) -> str:
        task_id = f"dummy-{uuid.uuid4().hex[:12]}"
        self._tasks[task_id] = {"prompt": request.prompt, "ticks": 0, "width": request.width, "height": request.height}
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
        object_key = f"generated/{provider_task_id}.{ext}"

        # 图片类型：生成真实 PNG 并上传到对象存储，前端可展示
        if self._kind == TaskKind.IMAGE:
            try:
                from provider_adapters.storage import get_storage

                png_bytes = _make_png(task["width"], task["height"], task["prompt"])
                storage = get_storage()
                await storage.upload(object_key, png_bytes, "image/png")
            except Exception:
                # 对象存储不可用时降级：仍返回 object_key，前端会拿到 404 但不阻塞任务流程
                pass

        return VisionResult(
            status=ProviderTaskStatus.SUCCESS,
            object_key=object_key,
            mime_type=f"image/{ext}" if self._kind == TaskKind.IMAGE else f"video/{ext}",
            width=task["width"],
            height=task["height"],
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
