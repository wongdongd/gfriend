"""素材路由：上传预签名 URL、媒体元数据。"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user
from api.core.error_codes import AppError, ErrorCode
from db.models.user import User
from shared.config import settings
from shared.database import get_db

router = APIRouter()


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str
    character_id: Optional[str] = None


@router.post("/upload-url")
async def create_upload_url(req: UploadUrlRequest, user: User = Depends(get_current_user)):
    """获取角色参考图的上传预签名 URL（前端直传对象存储）。"""
    from provider_adapters.storage import get_storage

    storage = get_storage()
    ext = req.filename.rsplit(".", 1)[-1] if "." in req.filename else "bin"
    object_key = f"uploads/{user.id}/{uuid.uuid4().hex}.{ext}"
    url = await storage.presigned_put_url(object_key, settings.s3_presign_expires, req.content_type)
    return {"upload_url": url, "object_key": object_key, "expires_in": settings.s3_presign_expires}


class AssetConfirmRequest(BaseModel):
    object_key: str
    content_type: str
    size_bytes: Optional[int] = None
    character_id: Optional[str] = None


@router.post("/confirm")
async def confirm_asset(req: AssetConfirmRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """确认上传完成，创建素材记录。"""
    from db.models.asset import Asset, AssetSource, AssetType
    from db.models.conversation import SafetyStatus

    asset = Asset(
        owner_id=user.id,
        character_id=uuid.UUID(req.character_id) if req.character_id else None,
        type=AssetType.REFERENCE_IMAGE,
        source=AssetSource.USER_UPLOAD,
        object_key=req.object_key,
        mime_type=req.content_type,
        size_bytes=req.size_bytes,
        safety_status=SafetyStatus.PENDING,
    )
    db.add(asset)
    await db.commit()
    return {"id": str(asset.id), "object_key": asset.object_key}


@router.get("/{asset_id}/url")
async def get_signed_url(asset_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取素材的短期签名访问 URL。"""
    from db.models.asset import Asset
    from db.models.conversation import SafetyStatus
    from sqlalchemy import select

    result = await db.execute(select(Asset).where(Asset.id == asset_id, Asset.owner_id == user.id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise AppError(ErrorCode.RESOURCE_ASSET_NOT_FOUND)
    if asset.safety_status == SafetyStatus.BLOCKED:
        raise AppError(ErrorCode.ASSET_BLOCKED)

    from provider_adapters.storage import get_storage

    storage = get_storage()
    url = await storage.presigned_get_url(asset.object_key, settings.s3_presign_expires)
    return {"url": url, "expires_in": settings.s3_presign_expires}
