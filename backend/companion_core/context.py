"""上下文组装。

对应实现方案第 6 节：companion 模块将角色人格、边界、近期消息和检索记忆
组装为受控上下文，调用语言模型并执行输出安全检查。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from db.models.character import Character
from db.models.conversation import Message, MessageRole


@dataclass
class ConversationContext:
    """组装好的受控上下文。"""

    system_prompt: str
    messages: list[dict] = field(default_factory=list)
    # 快照字段（用于审计）
    model_id: str | None = None
    template_version: str | None = None
    policy_version: str | None = None


def assemble_context(
    character: Character,
    recent_messages: list[Message],
    confirmed_memories: list[str] | None = None,
    conversation_summary: str | None = None,
    model_id: str | None = None,
) -> ConversationContext:
    """将角色档案、近期对话、已确认记忆组装为 LLM 上下文。

    近期消息数量有限制（默认最近 20 条），避免上下文过长。
    """
    from companion_core.prompt_builder import build_system_prompt

    system_prompt = build_system_prompt(
        character=character,
        confirmed_memories=confirmed_memories,
        conversation_summary=conversation_summary,
    )

    # 近期消息转为 LLM 格式
    messages: list[dict] = []
    for msg in recent_messages[-20:]:  # 最近 20 条
        if msg.role == MessageRole.SYSTEM:
            continue
        messages.append({"role": msg.role.value, "content": msg.content})

    return ConversationContext(
        system_prompt=system_prompt,
        messages=messages,
        model_id=model_id or character.model_params or None,
        policy_version="v1",
    )
