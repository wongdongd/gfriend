"""模板路由：获取关系、人格、场景和风格模板。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from db.models.template import Template, TemplateType
from db.models.user import User
from shared.database import get_db

router = APIRouter()


@router.get("")
async def list_templates(
    type: TemplateType | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取已发布的模板列表。"""
    stmt = select(Template).where(Template.is_enabled.is_(True), Template.is_published.is_(True))
    if type:
        stmt = stmt.where(Template.type == type)
    stmt = stmt.order_by(Template.sort_order, Template.created_at)
    result = await db.execute(stmt)
    return {
        "items": [
            {
                "id": str(t.id),
                "type": t.type.value,
                "code": t.code,
                "display_config": t.display_config,
                "preview_url": t.preview_url,
            }
            for t in result.scalars().all()
        ]
    }
