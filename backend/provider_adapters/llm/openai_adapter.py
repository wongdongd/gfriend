"""OpenAI LLM 适配器实现。

基于 ``openai`` SDK，支持流式与非流式补全、文本嵌入。
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from provider_adapters.llm.base import LLMAdapter, LLMRequest, LLMResponse, LLMUsage


class OpenAILLMAdapter(LLMAdapter):
    """OpenAI 兼容适配器（也适用于兼容 OpenAI 接口的其他供应商）。"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._embedding_model = embedding_model

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        resp = await self._client.chat.completions.create(
            model=request.model or self._model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            stream=False,
        )
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            usage=LLMUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=request.model or self._model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=self._embedding_model,
            input=texts,
        )
        return [item.embedding for item in resp.data]
