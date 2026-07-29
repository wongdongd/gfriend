"""视觉模型适配器工厂。"""
from __future__ import annotations

from provider_adapters.vision.base import (
    ProviderTaskStatus,
    TaskKind,
    VisionAdapter,
    VisionRequest,
    VisionResult,
)
from provider_adapters.vision.dummy import DummyVisionAdapter


def get_image_adapter() -> VisionAdapter:
    from shared.config import settings

    if settings.image_provider == "dummy" or not settings.image_api_key:
        return DummyVisionAdapter(kind=TaskKind.IMAGE)
    # TODO: 接入真实图片模型（如 DALL-E、Stable Diffusion 等）
    return DummyVisionAdapter(kind=TaskKind.IMAGE)


def get_video_adapter() -> VisionAdapter:
    from shared.config import settings

    if settings.video_provider == "dummy" or not settings.video_api_key:
        return DummyVisionAdapter(kind=TaskKind.VIDEO)
    # TODO: 接入真实视频模型
    return DummyVisionAdapter(kind=TaskKind.VIDEO)


__all__ = [
    "VisionAdapter",
    "VisionRequest",
    "VisionResult",
    "TaskKind",
    "ProviderTaskStatus",
    "get_image_adapter",
    "get_video_adapter",
]
