"""内容安全审核适配器抽象基类。

对应实现方案第 6 节、第 11 节：
文本输入、角色档案、上传素材和生成结果均需进行分级内容安全检查。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class SafetyVerdict(str, Enum):
    """审核结论。"""

    PASS = "pass"
    FLAG = "flag"  # 标记但放行
    BLOCK = "block"  # 拦截
    REVIEW = "review"  # 需人工审核


class CrisisLevel(str, Enum):
    """危机等级。"""

    NONE = "none"
    LOW = "low"
    HIGH = "high"  # 高风险：自伤/他伤，需切换安全响应策略


@dataclass
class SafetyCheckResult:
    """安全检查结果。"""

    verdict: SafetyVerdict = SafetyVerdict.PASS
    crisis_level: CrisisLevel = CrisisLevel.NONE
    # 命中的风险类型（spam / harassment / hate / sexual / violence / self_harm ...）
    flagged_categories: list[str] = field(default_factory=list)
    # 置信度（0-1）
    confidence: float = 0.0
    # 原始返回
    raw: dict = field(default_factory=dict)


class SafetyAdapter(ABC):
    """内容安全审核适配器抽象基类。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """供应商标识。"""

    @abstractmethod
    async def check_text(self, text: str, context: str = "user_input") -> SafetyCheckResult:
        """审核文本。context 可为 user_input / character_output / character_profile。"""

    @abstractmethod
    async def check_image(self, object_key: str) -> SafetyCheckResult:
        """审核图片（传入对象存储 key）。"""

    @abstractmethod
    async def check_video(self, object_key: str) -> SafetyCheckResult:
        """审核视频。"""
