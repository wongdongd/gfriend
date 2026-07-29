"""视觉模型适配器抽象基类。

对应实现方案第 7 节：
模型适配器统一提供 submit / getStatus / cancel / normalizeResult / estimateCost。
图片、视频使用独立队列。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class TaskKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class ProviderTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VisionRequest:
    """视觉生成请求。"""

    prompt: str
    kind: TaskKind = TaskKind.IMAGE
    # 角色视觉设定（注入到提示词）
    character_visual_prompt: str = ""
    # 风格模板提示词片段
    style_snippet: str = ""
    # 负面提示词
    negative_prompt: str = ""
    # 尺寸/分辨率
    width: int = 1024
    height: int = 1024
    # 参考图（object_key 列表）
    reference_keys: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass
class VisionResult:
    """视觉生成结果。"""

    status: ProviderTaskStatus
    # 生成的素材 object_key（成功后由 Worker 写入对象存储）
    object_key: str | None = None
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    # 供应商返回的原始结果
    raw: dict = field(default_factory=dict)
    error: str | None = None


class VisionAdapter(ABC):
    """视觉模型适配器抽象基类。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """供应商标识。"""

    @abstractmethod
    async def submit(self, request: VisionRequest) -> str:
        """提交生成任务，返回供应商任务 ID。"""

    @abstractmethod
    async def get_status(self, provider_task_id: str) -> VisionResult:
        """查询任务状态与结果。"""

    @abstractmethod
    async def cancel(self, provider_task_id: str) -> bool:
        """取消任务。返回是否成功取消。"""

    @abstractmethod
    def normalize_result(self, raw: dict, kind: TaskKind) -> VisionResult:
        """将供应商原始结果归一化为 ``VisionResult``。"""

    @abstractmethod
    def estimate_cost(self, request: VisionRequest) -> int:
        """估算积分消耗。"""
