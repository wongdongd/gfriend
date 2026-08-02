"""会话与消息路由：发送消息并流式接收角色回复。

对应实现方案第 6 节：
- 鉴权、限流与输入安全检查 → 检索记忆 → 组装上下文 → 流式生成 → 保存消息、输出审核、生成记忆候选。
"""
from __future__ import annotations

import json
import logging
import uuid

from companion_core.context import assemble_context
from companion_core.memory_retrieval import retrieve_memories
from companion_core.safety_guard import (
    check_input_safety,
    check_output_safety,
    get_crisis_response,
    should_trigger_crisis_response,
)
from db.models.character import Character, CharacterStatus
from db.models.conversation import Conversation, Message, MessageFeedback, MessageRole, SafetyStatus
from db.models.user import User
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from provider_adapters.llm import get_llm_adapter
from provider_adapters.llm.base import LLMMessage, LLMRequest
from provider_adapters.safety import SafetyVerdict, get_safety_adapter
from pydantic import BaseModel
from shared.config import settings
from shared.database import async_session_factory, get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user
from api.core.error_codes import AppError, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def _pick_locale(accept_language: str) -> str:
    """从 Accept-Language 推断受支持的语言，默认英文。"""
    for part in accept_language.split(","):
        code = part.split(";")[0].strip().lower()
        if code in ("en", "zh", "zh-cn", "zh-tw"):
            return "zh" if code.startswith("zh") else "en"
        if code.startswith("ja"):
            return "ja"
        if code.startswith("es"):
            return "es"
    return "en"


async def _get_character(db: AsyncSession, character_id: uuid.UUID, user: User) -> Character:
    """获取并校验角色归属。"""
    result = await db.execute(
        select(Character).where(Character.id == character_id, Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    if not character or character.status == CharacterStatus.DELETED:
        raise AppError(ErrorCode.RESOURCE_CHARACTER_NOT_FOUND)
    return character


async def _get_or_create_conversation(
    db: AsyncSession, character_id: uuid.UUID, user_id: uuid.UUID, given_id: str | None
) -> Conversation:
    """查找已有会话，不存在则创建。"""
    if given_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == uuid.UUID(given_id), Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv
    # 取最近一个会话
    result = await db.execute(
        select(Conversation)
        .where(Conversation.character_id == character_id, Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    conv = result.scalar_one_or_none()
    if conv:
        return conv
    conv = Conversation(character_id=character_id, user_id=user_id)
    db.add(conv)
    await db.flush()
    return conv


async def _build_user_content(
    db: AsyncSession, user_id: uuid.UUID, text: str, attachment_ids: list[str] | None
) -> str | list[dict]:
    """将文本 + 附件组装为 LLM 多模态 content 格式。"""
    if not attachment_ids:
        return text

    from db.models.asset import Asset
    from provider_adapters.storage import get_storage

    storage = get_storage()
    asset_ids = [uuid.UUID(aid) for aid in attachment_ids]
    result = await db.execute(
        select(Asset).where(Asset.id.in_(asset_ids), Asset.owner_id == user_id)
    )
    assets = result.scalars().all()

    image_parts: list[dict] = []
    for asset in assets:
        if not asset.object_key:
            continue
        try:
            img_url = await storage.presigned_get_url(asset.object_key, settings.s3_presign_expires)
            image_parts.append({"type": "image_url", "image_url": {"url": img_url}})
        except Exception:
            logger.warning("Failed to generate presigned URL for asset %s", asset.id)

    if image_parts:
        return [{"type": "text", "text": text}] + image_parts
    return text


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------


class SendMessageRequest(BaseModel):
    content: str
    conversation_id: str | None = None
    attachment_ids: list[str] | None = None


class FeedbackRequest(BaseModel):
    feedback: MessageFeedback
    note: str | None = None


@router.get("/{character_id}/messages")
async def list_messages(
    character_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    before: str | None = None,
):
    """获取会话消息历史。"""
    character = await _get_character(db, character_id, user)
    result = await db.execute(
        select(Conversation)
        .where(Conversation.character_id == character.id)
        .order_by(Conversation.created_at.desc())
        .limit(1)
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
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "feedback": m.feedback.value,
                "created_at": m.created_at.isoformat(),
                "attachments": getattr(m, "attachments", None),
            }
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
    高风险危机场景切换为安全响应；被 BLOCK 的消息直接拒绝返回。
    """
    character = await _get_character(db, character_id, user)
    conversation = await _get_or_create_conversation(
        db, character.id, user.id, req.conversation_id
    )

    # 1. 保存用户消息
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=req.content,
        attachments=req.attachment_ids or None,
    )
    db.add(user_msg)
    await db.flush()

    # 2. 输入安全检查（BLOCK 级别直接拒绝，不进入生成流程）
    safety_adapter = get_safety_adapter()
    input_check = await check_input_safety(safety_adapter, req.content)

    if input_check.verdict == SafetyVerdict.BLOCK:
        user_msg.safety_status = SafetyStatus.BLOCKED
        await db.commit()
        raise AppError(ErrorCode.ASSET_BLOCKED)

    # 3. 危机场景：直接返回安全响应，不进入角色扮演
    if should_trigger_crisis_response(input_check):
        locale = _pick_locale(request.headers.get("accept-language", ""))
        crisis_text = get_crisis_response(locale)
        assistant_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=crisis_text,
            policy_version="v1",
            safety_status=SafetyStatus.FLAGGED,
        )
        db.add(assistant_msg)
        await db.commit()

        async def crisis_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': crisis_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_msg.id), 'crisis': True, 'attachments': []})}\n\n"

        return StreamingResponse(crisis_stream(), media_type="text/event-stream")

    # 4. 检索已确认记忆
    confirmed_memories = await retrieve_memories(db, user.id, character.id, req.content)
    memory_texts = [m.content for m in confirmed_memories]

    # 5. 获取近期消息
    recent_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    recent_messages = list(reversed(recent_result.scalars().all()))

    # 6. 组装上下文
    ctx = assemble_context(
        character=character,
        recent_messages=recent_messages,
        confirmed_memories=memory_texts,
    )

    # 7. 组装用户消息内容（文本 + 多模态附件）
    user_content = await _build_user_content(db, user.id, req.content, req.attachment_ids)

    # 8. 构造 LLM 请求
    llm = get_llm_adapter()
    llm_request = LLMRequest(
        messages=[LLMMessage(role="system", content=ctx.system_prompt)]
        + [LLMMessage(role=m["role"], content=m["content"]) for m in ctx.messages]
        + [LLMMessage(role="user", content=user_content)],
        temperature=0.8,
    )

    # 9. SSE 流式生成
    async def generate():
        full_text = ""
        try:
            async for token in llm.stream(llm_request):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # 输出安全检查
            output_check = await check_output_safety(safety_adapter, full_text)

            # 使用独立 session 保存角色消息
            async with async_session_factory() as save_session:
                assistant_msg = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=full_text,
                    model_id=llm.provider_name,
                    policy_version="v1",
                    safety_status=(
                        SafetyStatus.FLAGGED
                        if output_check.verdict != SafetyVerdict.PASS
                        else SafetyStatus.PASS
                    ),
                )
                save_session.add(assistant_msg)
                await save_session.commit()
                msg_id = str(assistant_msg.id)

            yield f"data: {json.dumps({'type': 'done', 'message_id': msg_id, 'safety': output_check.verdict.value, 'attachments': []})}\n\n"
        except Exception:
            logger.exception("SSE generation failed")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Internal error occurred'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{character_id}/messages/{message_id}/feedback")
async def feedback_message(
    character_id: uuid.UUID,
    message_id: uuid.UUID,
    req: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对角色回复进行喜欢/不喜欢/调整语气反馈。"""
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Message.id == message_id, Conversation.user_id == user.id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise AppError(ErrorCode.RESOURCE_MESSAGE_NOT_FOUND)
    message.feedback = req.feedback
    message.feedback_note = req.note
    await db.commit()
    return {"ok": True}
