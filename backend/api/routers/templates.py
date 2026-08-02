"""模板路由：获取关系、人格、场景和风格模板。"""
from __future__ import annotations

from db.models.template import Template, TemplateType
from db.models.user import User
from fastapi import APIRouter, Depends, Query
from shared.database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user

router = APIRouter()


@router.get("")
async def list_templates(
    type_: TemplateType | None = Query(None, alias="type"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取已发布的模板列表。"""
    stmt = select(Template).where(Template.is_enabled.is_(True), Template.is_published.is_(True))
    if type_:
        stmt = stmt.where(Template.type == type_)
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
