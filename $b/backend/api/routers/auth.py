"""认证路由：邮箱注册/登录、OAuth 提供商、令牌刷新。"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.error_codes import AppError, ErrorCode
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from db.models.user import AgeStatus, AuthIdentity, AuthProvider, User
from shared.database import get_db

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """邮箱注册。"""
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise AppError(ErrorCode.AUTH_EMAIL_TAKEN)
    user = User(email=req.email, email_verified=False, password_hash=hash_password(req.password), display_name=req.display_name, age_status=AgeStatus.UNCONFIRMED)
    db.add(user)
    await db.flush()
    identity = AuthIdentity(user_id=user.id, provider=AuthProvider.EMAIL, provider_account_id=req.email, provider_email=req.email)
    db.add(identity)
    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id), user_id=str(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """邮箱登录。"""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise AppError(ErrorCode.AUTH_INVALID_CREDENTIALS)
    if not user.is_active or user.is_deleted:
        raise AppError(ErrorCode.AUTH_ACCOUNT_DISABLED)
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id), user_id=str(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """刷新访问令牌。"""
    payload = decode_token(req.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise AppError(ErrorCode.AUTH_REFRESH_INVALID)
    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AppError(ErrorCode.AUTH_USER_INVALID)
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id), user_id=str(user.id))


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
