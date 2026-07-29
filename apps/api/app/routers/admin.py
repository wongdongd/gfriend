"""管理后台路由：用户、模板、审核、任务、运营看板。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_operator
from db.models.user import User
from shared.database import get_db

router = APIRouter()


@router.get("/dashboard")
async def dashboard(user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    """运营看板：基础统计。"""
    from db.models.character import Character
    from db.models.generation import GenerationTask
    from db.models.billing import Order
    from db.models.safety import SafetyEvent

    # 用户总数
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    # 角色总数
    total_characters = (await db.execute(select(func.count(Character.id)))).scalar() or 0
    # 任务总数
    total_tasks = (await db.execute(select(func.count(GenerationTask.id)))).scalar() or 0
    # 待处理安全事件
    pending_safety = (await db.execute(select(func.count(SafetyEvent.id)).where(SafetyEvent.disposition == "pending"))).scalar() or 0

    return {
        "total_users": total_users,
        "total_characters": total_characters,
        "total_tasks": total_tasks,
        "pending_safety_events": pending_safety,
    }


@router.get("/users")
async def list_users(
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """用户列表。"""
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset))
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role.value,
                "age_status": u.age_status.value,
                "is_active": u.is_active,
                "credits_balance": u.credits_balance,
                "created_at": u.created_at.isoformat(),
            }
            for u in result.scalars().all()
        ]
    }


@router.get("/safety-events")
async def list_safety_events(
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
):
    """安全事件列表。"""
    from db.models.safety import SafetyEvent

    result = await db.execute(select(SafetyEvent).order_by(SafetyEvent.created_at.desc()).limit(limit))
    return {
        "items": [
            {
                "id": str(e.id),
                "risk_type": e.risk_type.value,
                "severity": e.severity,
                "disposition": e.disposition.value,
                "created_at": e.created_at.isoformat(),
            }
            for e in result.scalars().all()
        ]
    }
