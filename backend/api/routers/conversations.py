"""会话与消息路由：发送消息并流式接收角色回复。

对应实现方案第 6 节：
- 鉴权、限流与输入安全检查 → 检索记忆 → 组装上下文 → 流式生成 → 保存消息、输出审核、生成记忆候选。
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user
from api.core.error_codes import AppError, ErrorCode
from companion_core.context import assemble_context
from companion_core.memory_retrieval import retrieve_memories
from companion_core.safety_guard import (
    check_input_safety,
    check_output_safety,
    get_crisis_response,
    should_trigger_crisis_response,
)
from db.models.character import Character, CharacterStatus
from db.models.conversation import Conversation, Message, MessageFeedback, MessageRole
from db.models.user import User
from provider_adapters.llm import get_llm_adapter
from provider_adapters.safety import get_safety_adapter
from shared.database import async_session_factory, get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# 从 Accept-Language 推断受支持的语言（与前端 locales 一致），默认英文（海外优先）
def pick_locale(accept_language: str) -> str:
    for part in accept_language.split(","):
        code = part.split(";")[0].strip().lower()
        if code in ("en", "zh", "zh-cn", "zh-tw"):
            return "zh" if code.startswith("zh") else "en"
        if code.startswith("ja"):
            return "ja"
        if code.startswith("es"):
            return "es"
    return "en"


class SendMessageRequest(BaseModel):
    content: str
    conversation_id: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    feedback: str
    created_at: str


async def _get_character(db: AsyncSession, character_id: uuid.UUID, user: User) -> Character:
    result = await db.execute(select(Character).where(Character.id == character_id, Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character or character.status == CharacterStatus.DELETED:
        raise AppError(ErrorCode.RESOURCE_CHARACTER_NOT_FOUND)
    return character


@router.get("/{character_id}/messages")
async def list_messages(
    character_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    before: Optional[str] = None,
):
    """获取会话消息历史。"""
    character = await _get_character(db, character_id, user)
    result = await db.execute(
        select(Conversation).where(Conversation.character_id == character.id).order_by(Conversation.created_at.desc()).limit(1)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return {"conversation_id": None, "messages": []}
    stmt = select(Message).where(Message.conversation_id == conversation.id)
    if before:
        stmt = stmt.where(Message.id < uuid.UUID(before))
    stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    messages = list(reversed(result.scalars().all()))
    return {
        "conversation_id": str(conversation.id),
        "messages": [
            {"id": str(m.id), "role": m.role.value, "content": m.content, "feedback": m.feedback.value, "created_at": m.created_at.isoformat()}
            for m in messages
        ],
    }


@router.post("/{character_id}/messages")
async def send_message(
    character_id: uuid.UUID,
    req: SendMessageRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息并流式接收角色回复（SSE）。

    流程：保存用户消息 → 输入安全检查 → 检索记忆 → 组装上下文 → 流式生成 → 保存角色消息。
    高风险危机场景切换为安全响应。
    """
    character = await _get_character(db, character_id, user)

    # 获取或创建会话
    if req.conversation_id:
        conv_result = await db.execute(select(Conversation).where(Conversation.id == uuid.UUID(req.conversation_id), Conversation.user_id == user.id))
        conversation = conv_result.scalar_one_or_none()
    else:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.character_id == character.id, Conversation.user_id == user.id).order_by(Conversation.created_at.desc()).limit(1)
        )
        conversation = conv_result.scalar_one_or_none()
    if not conversation:
        conversation = Conversation(character_id=character.id, user_id=user.id)
        db.add(conversation)
        await db.flush()

    # 保存用户消息
    user_msg = Message(conversation_id=conversation.id, role=MessageRole.USER, content=req.content)
    db.add(user_msg)
    await db.flush()

    # 输入安全检查
    safety_adapter = get_safety_adapter()
    input_check = await check_input_safety(safety_adapter, req.content)

    # 危机场景：直接返回安全响应，不进入角色扮演
    if should_trigger_crisis_response(input_check):
        crisis_text = get_crisis_response(pick_locale(request.headers.get("accept-language", "")))
        assistant_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=crisis_text,
            policy_version="v1",
        )
        db.add(assistant_msg)
        await db.commit()

        async def crisis_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': crisis_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_msg.id), 'crisis': True})}\n\n"

        return StreamingResponse(crisis_stream(), media_type="text/event-stream")

    # 检索已确认记忆
    confirmed_memories = await retrieve_memories(db, user.id, character.id, req.content)
    memory_texts = [m.content for m in confirmed_memories]

    # 获取近期消息
    recent_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.desc()).limit(20)
    )
    recent_messages = list(reversed(recent_result.scalars().all()))

    # 组装上下文
    context = assemble_context(
        character=character,
        recent_messages=recent_messages,
        confirmed_memories=memory_texts,
    )

    # 调用 LLM
    from provider_adapters.llm.base import LLMMessage, LLMRequest

    llm = get_llm_adapter()
    llm_request = LLMRequest(
        messages=[LLMMessage(role="system", content=context.system_prompt)] + [LLMMessage(role=m["role"], content=m["content"]) for m in context.messages] + [LLMMessage(role="user", content=req.content)],
        temperature=0.8,
    )

    async def generate():
        full_text = ""
        try:
            async for token in llm.stream(llm_request):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # 输出安全检查
            output_check = await check_output_safety(safety_adapter, full_text)

            # 使用独立 session 保存角色消息，避免 StreamingResponse 在请求
            # 返回后才执行导致原 session 已被 get_db 关闭的问题。
            async with async_session_factory() as save_session:
                assistant_msg = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=full_text,
                    model_id=llm.provider_name,
                    policy_version="v1",
                )
                save_session.add(assistant_msg)
                await save_session.commit()
                msg_id = str(assistant_msg.id)

            yield f"data: {json.dumps({'type': 'done', 'message_id': msg_id, 'safety': output_check.verdict.value})}\n\n"
        except Exception:
            logger.exception("SSE generation failed")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Internal error occurred'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


class FeedbackRequest(BaseModel):
    feedback: MessageFeedback
    note: Optional[str] = None


@router.post("/{character_id}/messages/{message_id}/feedback")
async def feedback_message(
    character_id: uuid.UUID,
    message_id: uuid.UUID,
    req: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对角色回复进行喜欢/不喜欢/调整语气反馈。"""
    result = await db.execute(select(Message).join(Conversation, Message.conversation_id == Conversation.id).where(Message.id == message_id, Conversation.user_id == user.id))
    message = result.scalar_one_or_none()
    if not message:
        raise AppError(ErrorCode.RESOURCE_MESSAGE_NOT_FOUND)
    message.feedback = req.feedback
    message.feedback_note = req.note
    await db.commit()
    return {"ok": True}
