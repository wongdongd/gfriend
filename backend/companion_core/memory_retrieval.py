"""记忆检索。

对应实现方案第 6 节实施约束：
- 只在用户和当前角色的命名空间检索记忆，默认最多注入少量高相关条目。
- 对敏感信息采用更严格策略：默认不自动保存，要求显式确认。
- 对用户删除操作同时删除向量和原文。
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.memory import Memory, MemoryStatus

# 默认注入的记忆数量上限（避免"记忆堆砌"）
DEFAULT_TOP_K = 5
# 相关度阈值
DEFAULT_THRESHOLD = 0.7


async def retrieve_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    character_id: uuid.UUID,
    query_text: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[Memory]:
    """检索与当前对话相关的已确认记忆。

    仅检索 status=CONFIRMED 的记忆，限定在 (user_id, character_id) 命名空间。
    使用 pgvector 的余弦距离排序；若嵌入不可用则回退为全文-like 匹配。
    """
    # 生成查询向量
    from provider_adapters.llm import get_llm_adapter

    adapter = get_llm_adapter()
    try:
        embeddings = await adapter.embed([query_text])
        query_vec = embeddings[0]
    except Exception:
        # 嵌入失败时回退为简单匹配
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.character_id == character_id,
                Memory.status == MemoryStatus.CONFIRMED,
                Memory.content.ilike(f"%{query_text[:50]}%"),
            )
            .limit(top_k)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # 使用 pgvector 余弦距离检索。
    # 关键：pgvector 查询一旦在事务中失败，整个事务即被 PostgreSQL 标记为 aborted，
    # 后续任何 SQL 都会报 "current transaction is aborted"。因此把 pgvector 尝试放到
    # 嵌套事务（savepoint）里，失败时仅回滚该 savepoint，再执行回退查询，避免污染外层事务。
    try:
        from pgvector.sqlalchemy import Vector
    except Exception:
        Vector = None  # noqa: N806 - 类名导入变量

    if Vector is not None:
        try:
            # 失败时异常会穿过 async with，自动回滚 savepoint，外层事务保持可用。
            async with db.begin_nested():
                stmt = (
                    select(Memory, Memory.embedding.cosine_distance(query_vec).label("distance"))
                    .where(
                        Memory.user_id == user_id,
                        Memory.character_id == character_id,
                        Memory.status == MemoryStatus.CONFIRMED,
                        Memory.embedding.isnot(None),
                    )
                    .order_by("distance")
                    .limit(top_k)
                )
                result = await db.execute(stmt)
                return [row[0] for row in result.all()]
        except Exception:
            # savepoint 已回滚，外层事务未受影响，随后执行回退查询。
            pass

    # pgvector 不可用或查询失败时回退为简单匹配
    stmt = (
        select(Memory)
        .where(
            Memory.user_id == user_id,
            Memory.character_id == character_id,
            Memory.status == MemoryStatus.CONFIRMED,
        )
        .limit(top_k)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def extract_memory_candidates(
    user_message: str,
    assistant_message: str,
) -> list[str]:
    """从对话中提取候选记忆摘要。

    返回的候选需经用户确认后才会被持久化为可用记忆。
    MVP 阶段使用 LLM 提取；此处先返回空列表，由 conversation 模块调用 LLM。
    """
    # 实际实现见 conversation 模块的 LLM 调用
    return []
