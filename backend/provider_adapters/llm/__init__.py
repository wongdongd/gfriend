"""LLM 适配器工厂。"""
from __future__ import annotations

from provider_adapters.llm.base import LLMAdapter, LLMRequest, LLMResponse, LLMUsage
from provider_adapters.llm.dummy import DummyLLMAdapter


def get_llm_adapter() -> LLMAdapter:
    """根据配置创建 LLM 适配器。"""
    from shared.config import settings

    if settings.llm_provider == "openai" and settings.llm_api_key:
        from provider_adapters.llm.openai_adapter import OpenAILLMAdapter

        return OpenAILLMAdapter(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url or None,
            embedding_model=settings.embedding_model,
        )
    return DummyLLMAdapter()


__all__ = ["LLMAdapter", "LLMRequest", "LLMResponse", "LLMUsage", "get_llm_adapter"]
