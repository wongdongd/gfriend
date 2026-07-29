"""对象存储适配器抽象基类。

对应实现方案第 9 节：私有媒体使用短期签名 URL。
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class StorageAdapter(ABC):
    """S3 兼容对象存储适配器。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """供应商标识。"""

    @abstractmethod
    async def upload(self, object_key: str, data: bytes, content_type: str) -> str:
        """上传文件，返回 object_key。"""

    @abstractmethod
    async def download(self, object_key: str) -> bytes:
        """下载文件。"""

    @abstractmethod
    async def delete(self, object_key: str) -> bool:
        """删除文件。"""

    @abstractmethod
    async def presigned_get_url(self, object_key: str, expires: int) -> str:
        """生成短期签名 GET URL。"""

    @abstractmethod
    async def presigned_put_url(self, object_key: str, expires: int, content_type: str) -> str:
        """生成短期签名 PUT URL（供前端直传）。"""
