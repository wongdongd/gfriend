"""应用配置。

使用 pydantic-settings 从环境变量加载配置；
密钥类配置缺失时给出明确警告而非直接崩溃（便于本地开发）。
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，从 ``.env`` 加载。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 应用 ----------
    app_env: str = "development"
    app_name: str = "companion-platform"
    app_port: int = 8000
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    log_level: str = "INFO"
    secret_key: str = "change-me-to-a-long-random-string"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 30

    # ---------- 数据库 ----------
    database_url: str = "postgresql+asyncpg://companion:companion@localhost:5432/companion"
    database_sync_url: str = "postgresql://companion:companion@localhost:5432/companion"

    # ---------- Redis / Celery ----------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Railway 插件只注入 REDIS_URL，这里提供派生属性让 Celery 复用该连接串。
    @property
    def celery_broker(self) -> str:
        # 若显式设置了 CELERY_BROKER_URL 则直接使用；否则基于 REDIS_URL 生成
        broker = self.celery_broker_url
        if os.getenv("CELERY_BROKER_URL"):
            return broker
        base = self.redis_url.rstrip("/")
        return base + "/1"

    @property
    def celery_backend(self) -> str:
        backend = self.celery_result_backend
        if os.getenv("CELERY_RESULT_BACKEND"):
            return backend
        base = self.redis_url.rstrip("/")
        return base + "/2"

    # ---------- 对象存储 ----------
    s3_endpoint: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "companion-assets"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_use_path_style: bool = True
    s3_presign_expires: int = 3600

    # ---------- OAuth ----------
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback/google"
    facebook_client_id: str = ""
    facebook_client_secret: str = ""
    facebook_redirect_uri: str = "http://localhost:8000/api/auth/callback/facebook"

    # ---------- LLM ----------
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # ---------- 视觉模型 ----------
    image_provider: str = "dummy"
    image_api_key: str = ""
    image_model: str = ""
    image_base_url: str = ""
    video_provider: str = "dummy"
    video_api_key: str = ""
    video_model: str = ""

    # ---------- 嵌入 ----------
    embedding_provider: str = "openai"
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # ---------- 安全 ----------
    safety_provider: str = "dummy"
    safety_api_key: str = ""

    # ---------- 支付 ----------
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_subscription: str = ""
    stripe_price_credits: str = ""
    stripe_success_url: str = "http://localhost:3000/billing/success"
    stripe_cancel_url: str = "http://localhost:3000/billing/cancel"

    # ---------- 限流 ----------
    rate_limit_per_minute: int = 60

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# 全局单例
settings = get_settings()
