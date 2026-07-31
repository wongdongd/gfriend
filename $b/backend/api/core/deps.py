"""FastAPI 依赖注入：当前用户、数据库会话、管理员校验。"""
from __future__ import annotations

import uuid

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import AppError, ErrorCode
from app.core.security import decode_token
from db.models.user import User, UserRole
from shared.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 Bearer 令牌解析当前用户。"""
    if creds is None or creds.scheme.lower() != "bearer":
        raise AppError(ErrorCode.AUTH_TOKEN_MISSING)
    payload = decode_token(creds.credentials)
    if payload is None or payload.get("type") != "access":
        raise AppError(ErrorCode.AUTH_TOKEN_INVALID)
    user_id = payload.get("sub")
    if not user_id:
        raise AppError(ErrorCode.AUTH_TOKEN_PAYLOAD_INVALID)
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or user.is_deleted:
        raise AppError(ErrorCode.AUTH_USER_INVALID)
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求当前用户为管理员。"""
    if user.role != UserRole.ADMIN:
        raise AppError(ErrorCode.PERMISSION_ADMIN_REQUIRED)
    return user


async def require_operator(user: User = Depends(get_current_user)) -> User:
    """要求当前用户为管理员或运营。"""
    if user.role not in (UserRole.ADMIN, UserRole.OPERATOR):
        raise AppError(ErrorCode.PERMISSION_OPERATOR_REQUIRED)
    return user
