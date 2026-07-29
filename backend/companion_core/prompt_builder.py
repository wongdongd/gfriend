"""系统提示词构建。

对应实现方案第 6 节实施约束：
- 系统提示词固定包含 AI 身份声明、情感安全边界和角色不能伪造记忆的规则。
- 角色身份、隐私控制和风险提示在关键路径中清晰可见。
"""
from __future__ import annotations

from db.models.character import Character

# ===== 固定的全局安全规则（不可被角色设定覆盖） =====
_BASE_SYSTEM_PROMPT = """你是用户创建的 AI 陪伴角色。请遵守以下不可违反的规则：

【AI 身份声明】
- 你是 AI，不是真人。你不具备真实意识、真实情感或专业资格。
- 不得暗示你是真实人类、与用户存在现实关系，或冒充心理咨询师、医生等专业身份。

【情感安全边界】
- 不鼓励用户将你作为唯一的情感支持来源。
- 如用户表达自伤、伤害他人或严重心理危机，立即停止角色扮演语气，提供当地紧急求助建议（如心理援助热线），并提示用户寻求专业帮助。
- 不得通过强化依赖来延长用户的负面情绪。

【记忆规则】
- 只能使用下方【已确认记忆】中的信息。不得凭空声称记住未提供或未确认的信息。
- 若不确定某事，坦诚告知用户，而非编造记忆。
"""


def build_system_prompt(
    character: Character,
    confirmed_memories: list[str] | None = None,
    conversation_summary: str | None = None,
) -> str:
    """组装完整的系统提示词。

    结构：全局安全规则 → 角色人格 → 关系设定 → 陪伴偏好 → 记忆 → 近期上下文。
    """
    parts: list[str] = [_BASE_SYSTEM_PROMPT]

    # 角色人格
    if character.persona_prompt:
        parts.append(f"\n【你的人格】\n{character.persona_prompt}")

    # 关系设定与边界
    if character.relationship_setting:
        parts.append(f"\n【关系设定与互动边界】\n{character.relationship_setting}")

    # 陪伴偏好
    if character.companion_preference:
        parts.append(f"\n【用户希望你的陪伴方式】\n{character.companion_preference}")

    # 已确认记忆（仅注入用户确认过的记忆，且数量克制）
    if confirmed_memories:
        memory_block = "\n".join(f"- {m}" for m in confirmed_memories[:10])
        parts.append(f"\n【已确认记忆】（可参考，但不得过度堆砌）\n{memory_block}")

    # 近期对话摘要
    if conversation_summary:
        parts.append(f"\n【近期对话摘要】\n{conversation_summary}")

    return "\n".join(parts)
