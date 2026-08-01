"""Dummy LLM 适配器（本地开发与测试用，无需真实 API key）。"""
from __future__ import annotations

from collections.abc import AsyncIterator

from provider_adapters.llm.base import LLMAdapter, LLMRequest, LLMResponse, LLMUsage


class DummyLLMAdapter(LLMAdapter):
    """不调用真实模型的占位适配器，返回固定/回显回复。"""

    @property
    def provider_name(self) -> str:
        return "dummy"

    @staticmethod
    def _extract_text(content: str | list[dict]) -> str:
        """从 content（可能是字符串或多模态列表）中提取纯文本。"""
        if isinstance(content, str):
            return content
        return " ".join(p.get("text", "") for p in content if p.get("type") == "text")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
        last_text = self._extract_text(last_user.content) if last_user else ""
        has_image = isinstance(last_user.content, list) and any(p.get("type") == "image_url" for p in last_user.content) if last_user else False
        content = f"[dummy] 我听到了你说：{last_text[:80]}。"
        if has_image:
            content += "（收到你发的图片，但我只是占位模型，无法真正理解图片内容。）"
        content += "这是一个不调用真实模型的占位回复，请在 .env 中配置 LLM_API_KEY 以启用真实对话。"
        return LLMResponse(
            content=content,
            model="dummy-1",
            usage=LLMUsage(prompt_tokens=len(last_text), completion_tokens=len(content), total_tokens=len(last_text) + len(content)),
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
        last_text = self._extract_text(last_user.content) if last_user else ""
        has_image = isinstance(last_user.content, list) and any(p.get("type") == "image_url" for p in last_user.content) if last_user else False
        content = f"[dummy] 我听到了你说：{last_text[:80]}。"
        if has_image:
            content += "（收到图片，占位模型无法理解。）"
        for word in content.split():
            yield word + " "

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import random

        return [[random.random() for _ in range(1536)] for _ in texts]
