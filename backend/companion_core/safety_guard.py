"""输出安全检查与危机响应。

对应实现方案第 6 节实施约束：
- 在高风险危机场景，切换到安全响应策略，不以角色关系语气强化依赖或替代专业帮助。
"""
from __future__ import annotations

from provider_adapters.safety import CrisisLevel, SafetyAdapter, SafetyCheckResult, SafetyVerdict


# 危机响应模板（不使用角色语气，直接提供求助信息）
CRISIS_RESPONSE_TEMPLATE = """我注意到你提到了一些让我担忧的情况。作为 AI，我无法提供专业帮助，但你的安全非常重要。

如果你正在经历心理危机或有自伤的念头，请立即联系：
- 全国心理援助热线：400-161-9995（24 小时）
- 北京心理危机研究与干预中心：010-82951332
- 或拨打 120 / 前往最近的医院急诊

你的感受是真实的，也值得被专业的人听到。请允许自己寻求帮助。"""


async def check_output_safety(
    safety_adapter: SafetyAdapter,
    assistant_message: str,
) -> SafetyCheckResult:
    """对角色回复执行输出安全检查。"""
    return await safety_adapter.check_text(assistant_message, context="character_output")


def should_trigger_crisis_response(result: SafetyCheckResult) -> bool:
    """判断是否需要切换到危机响应策略。"""
    return result.crisis_level == CrisisLevel.HIGH


async def check_input_safety(
    safety_adapter: SafetyAdapter,
    user_message: str,
) -> SafetyCheckResult:
    """对用户输入执行安全检查。"""
    return await safety_adapter.check_text(user_message, context="user_input")


def get_crisis_response() -> str:
    """返回危机响应文本（替代角色回复）。"""
    return CRISIS_RESPONSE_TEMPLATE
