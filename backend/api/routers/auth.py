"""认证路由：邮箱注册/登录、OAuth 提供商、令牌刷新、登出。

Token 通过 httpOnly cookie 下发，同时也支持 Authorization header（兼容旧客户端）。
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_current_user
from api.core.error_codes import AppError, ErrorCode
from api.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_refresh_token_valid,
    revoke_refresh_token,
    store_refresh_token,
    verify_password,
)
from db.models.user import AgeStatus, AuthIdentity, AuthProvider, User
from shared.config import settings
from shared.database import get_db

router = APIRouter()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """将 token 写入 httpOnly Secure SameSite cookie。"""
    secure = settings.app_env != "development"
    access_max_age = settings.jwt_access_expire_minutes * 60
    refresh_max_age = settings.jwt_refresh_expire_days * 86400

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/api/auth/refresh",
    )


def _clear_auth_cookies(response: Response) -> None:
    """清除认证 cookie。"""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AgeConfirmRequest(BaseModel):
    is_adult: bool


@router.get("/providers")
async def list_providers():
    """获取可用登录方式。"""
    from shared.config import settings

    providers = [{"provider": "email", "label": "邮箱登录"}]
    if settings.google_client_id:
        providers.append({"provider": "google", "label": "Google 登录"})
    if settings.facebook_client_id:
        providers.append({"provider": "facebook", "label": "Facebook 登录"})
    return {"providers": providers}


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """邮箱注册。"""
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise AppError(ErrorCode.AUTH_EMAIL_TAKEN)
    user = User(email=req.email, email_verified=False, password_hash=hash_password(req.password), display_name=req.display_name, age_status=AgeStatus.UNCONFIRMED)
    db.add(user)
    await db.flush()
    identity = AuthIdentity(user_id=user.id, provider=AuthProvider.EMAIL, provider_account_id=req.email, provider_email=req.email)
    db.add(identity)
    await db.flush()
    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)
    await store_refresh_token(str(user.id), jti)
    await db.commit()
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user_id=str(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """邮箱登录。"""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise AppError(ErrorCode.AUTH_INVALID_CREDENTIALS)
    if not user.is_active or user.is_deleted:
        raise AppError(ErrorCode.AUTH_ACCOUNT_DISABLED)
    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)
    await store_refresh_token(str(user.id), jti)
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user_id=str(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """刷新访问令牌。

    校验 token 签名 + Redis 中是否仍有效（未被吊销），然后轮换 refresh token。
    """
    payload = decode_token(req.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise AppError(ErrorCode.AUTH_REFRESH_INVALID)
    user_id = payload["sub"]
    jti = payload.get("jti", "")

    # 检查 Redis 中的有效性
    if not await is_refresh_token_valid(user_id, jti):
        raise AppError(ErrorCode.AUTH_REFRESH_INVALID)

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AppError(ErrorCode.AUTH_USER_INVALID)

    # 吊销旧 token，签发新 token（refresh token rotation）
    await revoke_refresh_token(user_id, jti)
    access_token = create_access_token(user.id)
    new_refresh_token, new_jti = create_refresh_token(user.id)
    await store_refresh_token(str(user.id), new_jti)

    _set_auth_cookies(response, access_token, new_refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user_id=str(user.id),
    )


@router.post("/logout")
async def logout(response: Response, user: User = Depends(get_current_user)):
    """登出：吊销当前用户所有 refresh token + 清除 cookie。"""
    await revoke_refresh_token(str(user.id))
    _clear_auth_cookies(response)
    return {"ok": True}


@router.post("/age-confirm")
async def confirm_age(req: AgeConfirmRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """年龄确认（首次创建账户后执行）。"""
    user.age_status = AgeStatus.CONFIRMED if req.is_adult else AgeStatus.MINOR
    if req.is_adult and not user.terms_accepted_at:
        from datetime import datetime, timezone
        user.terms_accepted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"age_status": user.age_status.value}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息。"""
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "age_status": user.age_status.value,
        "role": user.role.value,
        "subscription_tier": user.subscription_tier,
        "credits_balance": user.credits_balance,
    }
