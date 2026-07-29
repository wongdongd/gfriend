"""对象存储适配器工厂。"""
from __future__ import annotations

from provider_adapters.storage.base import StorageAdapter


_storage: StorageAdapter | None = None


def get_storage() -> StorageAdapter:
    """全局单例（boto3 client 创建成本较高）。"""
    global _storage
    if _storage is not None:
        return _storage
    from shared.config import settings

    from provider_adapters.storage.s3_adapter import S3StorageAdapter

    _storage = S3StorageAdapter(
        endpoint_url=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        region=settings.s3_region,
        bucket=settings.s3_bucket,
        use_path_style=settings.s3_use_path_style,
    )
    return _storage


__all__ = ["StorageAdapter", "get_storage"]
