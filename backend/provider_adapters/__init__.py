"""provider_adapters：LLM / 视觉 / 支付 / 存储 / 安全 五类适配器。

所有适配器均以抽象基类定义接口，并提供可替换的供应商实现与本地 dummy 实现。
"""
from provider_adapters import llm, payment, safety, storage, vision

__all__ = ["llm", "vision", "payment", "storage", "safety"]
