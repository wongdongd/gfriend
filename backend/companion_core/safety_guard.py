"""输出安全检查与危机响应。

对应实现方案第 6 节实施约束：
- 在高风险危机场景，切换到安全响应策略，不以角色关系语气强化依赖或替代专业帮助。
- 危机热线按地区/语言返回，避免把单一国家号码硬编码到面向海外的产品里。
"""
from __future__ import annotations

from provider_adapters.safety import CrisisLevel, SafetyAdapter, SafetyCheckResult

# 危机响应模板（不使用角色语气，直接提供求助信息），按 locale 区分热线
CRISIS_RESPONSES: dict[str, str] = {
    "en": """I'm concerned about what you've shared. As an AI, I can't provide professional help, but your safety matters.

If you're in crisis or having thoughts of self-harm, please reach out:
- Your local emergency number (e.g. 911 in the US, 112 in the EU)
- 988 Suicide & Crisis Lifeline (US): call or text 988, 24/7
- findahelpline.com to locate a free, confidential service near you

Your feelings are real and deserve to be heard by a professional. Please consider reaching out.""",
    "zh": """我注意到你提到了一些让我担忧的情况。作为 AI，我无法提供专业帮助，但你的安全非常重要。

如果你正在经历心理危机或有自伤的念头，请立即联系：
- 全国心理援助热线：400-161-9995（24 小时）
- 北京心理危机研究与干预中心：010-82951332
- 或拨打 120 / 前往最近的医院急诊

你的感受是真实的，也值得被专业的人听到。请允许自己寻求帮助。""",
    "ja": """あなたのお話を伺って、心配になりました。AI である私には専門的な助けは提供できませんが、あなたの安全が何より大切です。

もし今、危機的な状況にある、あるいは自分を傷つけたい考えがある場合は、すぐにご相談ください：
- まもろうよ こころ 相談ダイヤル：0570-064-556（24 時間）
- ライフリンク（自殺予防）：0800-783-0565（24 時間・通話無料）
- 緊急の場合は 119（救急）へ

あなたの気持ちは本物です。専門の窓口に、ぜひ話してみてください。""",
    "es": """Me preocupa lo que me cuentas. Como IA no puedo ofrecerte ayuda profesional, pero tu seguridad es lo más importante.

Si estás en crisis o tienes pensamientos de hacerte daño, por favor busca apoyo:
- Tu número de emergencia local (en España, el 112)
- Línea de atención a la conducta suicida: 024 (24 h, gratuita)
- sanidad.gob.es para encontrar recursos cercanos

Tus sentimientos son reales y merecen ser escuchados por un profesional. Por favor, considera pedir ayuda.""",
}

# 受支持的 locale（与前端一致）
SUPPORTED_LOCALES = ("en", "zh", "ja", "es")


def get_crisis_response(locale: str = "en") -> str:
    """按地区/语言返回危机响应文本（替代角色回复）。未知 locale 回退到英文。"""
    return CRISIS_RESPONSES.get(locale, CRISIS_RESPONSES["en"])


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

