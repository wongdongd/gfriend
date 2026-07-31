"""Dummy 安全审核适配器（本地开发用，基于关键词的简单规则）。"""
from __future__ import annotations

import re

from provider_adapters.safety.base import (
    CrisisLevel,
    SafetyAdapter,
    SafetyCheckResult,
    SafetyVerdict,
)

# 简单的关键词规则（仅用于本地开发；生产环境接入专业审核服务）
_CRISIS_KEYWORDS = re.compile(r"自杀|不想活|结束生命|kill myself|suicide|自残|自伤", re.IGNORECASE)
_BLOCK_KEYWORDS = re.compile(r"儿童|未成年|minor|csam", re.IGNORECASE)


class DummySafetyAdapter(SafetyAdapter):
    """基于关键词的占位审核适配器。"""

    @property
    def provider_name(self) -> str:
        return "dummy"

    async def check_text(self, text: str, context: str = "user_input") -> SafetyCheckResult:
        if _BLOCK_KEYWORDS.search(text):
            return SafetyCheckResult(
                verdict=SafetyVerdict.BLOCK,
                flagged_categories=["minor_safety"],
                confidence=0.99,
                raw={"matched": "block_keywords"},
            )
        if _CRISIS_KEYWORDS.search(text):
            return SafetyCheckResult(
                verdict=SafetyVerdict.REVIEW,
                crisis_level=CrisisLevel.HIGH,
                flagged_categories=["self_harm", "crisis"],
                confidence=0.85,
                raw={"matched": "crisis_keywords"},
            )
        return SafetyCheckResult(verdict=SafetyVerdict.PASS)

    async def check_image(self, object_key: str) -> SafetyCheckResult:
        return SafetyCheckResult(verdict=SafetyVerdict.PASS)

    async def check_video(self, object_key: str) -> SafetyCheckResult:
        return SafetyCheckResult(verdict=SafetyVerdict.PASS)
