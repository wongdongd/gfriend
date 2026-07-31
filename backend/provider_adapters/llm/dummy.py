"""Dummy LLM 适配器（本地开发与测试用，无需真实 API key）。"""
from __future__ import annotations

from collections.abc import AsyncIterator

from provider_adapters.llm.base import LLMAdapter, LLMRequest, LLMResponse, LLMUsage


class DummyLLMAdapter(LLMAdapter):
    """不调用真实模型的占位适配器，返回固定/回显回复。"""

    @property
    def provider_name(self) -> str:
        return "dummy"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        last_user = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        content = f"[dummy] 我听到了你说：{last_user[:80]}。这是一个不调用真实模型的占位回复，请在 .env 中配置 LLM_API_KEY 以启用真实对话。"
        return LLMResponse(
            content=content,
            model="dummy-1",
            usage=LLMUsage(prompt_tokens=len(last_user), completion_tokens=len(content), total_tokens=len(last_user) + len(content)),
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        last_user = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        content = f"[dummy] 我听到了你说：{last_user[:80]}。"
        for word in content.split():
            yield word + " "

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import random

        return [[random.random() for _ in range(1536)] for _ in texts]
