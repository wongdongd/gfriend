"""安全工具：密码哈希、JWT 令牌、Refresh Token 吊销。"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext
from shared.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | uuid.UUID, extra: dict | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(subject: str | uuid.UUID) -> tuple[str, str]:
    """创建 refresh token 并返回 (token, jti)。

    jti（JWT ID）存储在 Redis 中，支持主动吊销。
    """
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    jti = uuid.uuid4().hex
    payload = {"sub": str(subject), "exp": expire, "type": "refresh", "jti": jti}
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token, jti


async def store_refresh_token(user_id: str, jti: str) -> None:
    """将 refresh token 的 jti 存入 Redis，TTL 与 token 过期时间一致。"""
    from shared.redis import get_redis

    r = await get_redis()
    ttl = settings.jwt_refresh_expire_days * 86400
    await r.set(f"refresh:{user_id}:{jti}", "1", ex=ttl)


async def revoke_refresh_token(user_id: str, jti: str | None = None) -> None:
    """吊销 refresh token。

    若提供 jti，仅吊销该特定 token；
    否则吊销该用户的所有 refresh token（如在修改密码后）。
    """
    from shared.redis import get_redis

    r = await get_redis()
    if jti:
        await r.delete(f"refresh:{user_id}:{jti}")
        # 加入黑名单直到原 token 自然过期
        await r.set(f"revoked:{jti}", "1", ex=settings.jwt_refresh_expire_days * 86400)
    else:
        # 扫描并删除该用户所有 refresh token
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor, match=f"refresh:{user_id}:*", count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break


async def is_refresh_token_valid(user_id: str, jti: str) -> bool:
    """检查 refresh token 是否仍有效（未吊销）。"""
    from shared.redis import get_redis

    r = await get_redis()
    # 先检查黑名单
    if await r.exists(f"revoked:{jti}"):
        return False
    # 再检查白名单
    return await r.exists(f"refresh:{user_id}:{jti}")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except Exception:
        return None
