"""LLM 适配器抽象基类。

对应实现方案第 2 节：语言模型使用适配器接口，便于替换供应商。
对话请求应同步快速返回；角色回复以流式方式呈现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class LLMMessage:
    """对话消息（适配器中性表示）。

    ``content`` 可以是纯文本字符串，也可以是 OpenAI 多模态格式的内容列表：
    ``[{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {"url": "..."}}]``
    """

    role: str  # "system" | "user" | "assistant"
    content: str | list[dict]


@dataclass
class LLMRequest:
    """LLM 请求。"""

    messages: list[LLMMessage] = field(default_factory=list)
    model: str | None = None
    temperature: float = 0.8
    top_p: float = 1.0
    max_tokens: int | None = None
    # 供应商透传参数
    extra: dict = field(default_factory=dict)


@dataclass
class LLMUsage:
    """token 用量。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """LLM 完整响应（非流式）。"""

    content: str
    model: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    finish_reason: str = "stop"


class LLMAdapter(ABC):
    """LLM 适配器抽象基类。"""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """非流式补全。"""

    @abstractmethod
    def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """流式补全，逐片段 yield 文本。"""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """文本嵌入向量（用于记忆检索）。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """供应商标识。"""
