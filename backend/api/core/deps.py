"""FastAPI 依赖注入：当前用户、数据库会话、管理员校验。

认证支持两种方式（优先级从高到低）：
1. Authorization: Bearer <token> header
2. access_token httpOnly cookie
"""
from __future__ import annotations

import uuid

from fastapi import Cookie, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.error_codes import AppError, ErrorCode
from api.core.security import decode_token
from db.models.user import User, UserRole
from shared.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def _get_token(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    access_token_cookie: str | None = Cookie(default=None, alias="access_token"),
) -> str | None:
    """提取 token：优先从 Authorization header，其次从 httpOnly cookie。"""
    if creds is not None and creds.scheme.lower() == "bearer":
        return creds.credentials
    return access_token_cookie


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    access_token_cookie: str | None = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 Bearer 令牌或 cookie 解析当前用户。"""
    token = await _get_token(request, creds, access_token_cookie)
    if token is None:
        raise AppError(ErrorCode.AUTH_TOKEN_MISSING)
    payload = decode_token(token)
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
