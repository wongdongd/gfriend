"""安全审核适配器工厂。"""
from __future__ import annotations

from provider_adapters.safety.base import (
    CrisisLevel,
    SafetyAdapter,
    SafetyCheckResult,
    SafetyVerdict,
)
from provider_adapters.safety.dummy import DummySafetyAdapter


def get_safety_adapter() -> SafetyAdapter:
    from shared.config import settings

    if settings.safety_provider == "dummy" or not settings.safety_api_key:
        return DummySafetyAdapter()
    # TODO: 接入专业审核服务（如 OpenAI Moderation、AWS Rekognition 等）
    return DummySafetyAdapter()


__all__ = [
    "SafetyAdapter",
    "SafetyCheckResult",
    "SafetyVerdict",
    "CrisisLevel",
    "get_safety_adapter",
]
