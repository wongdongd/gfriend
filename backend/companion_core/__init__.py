"""companion_core：上下文组装、记忆检索、安全编排。

将角色人格、边界、近期消息和检索记忆组装为受控上下文，
调用语言模型并执行输出安全检查。
"""
from companion_core.context import ConversationContext, assemble_context
from companion_core.memory_retrieval import retrieve_memories
from companion_core.prompt_builder import build_system_prompt
from companion_core.safety_guard import (
    check_input_safety,
    check_output_safety,
    get_crisis_response,
    should_trigger_crisis_response,
)

__all__ = [
    "ConversationContext",
    "assemble_context",
    "retrieve_memories",
    "build_system_prompt",
    "check_input_safety",
    "check_output_safety",
    "get_crisis_response",
    "should_trigger_crisis_response",
]
