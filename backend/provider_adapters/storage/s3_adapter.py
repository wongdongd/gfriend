"""S3 兼容对象存储适配器（基于 boto3，本地对接 MinIO）。"""
from __future__ import annotations

from provider_adapters.storage.base import StorageAdapter


class S3StorageAdapter(StorageAdapter):
    """S3 兼容适配器，支持 AWS S3、MinIO 等。"""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str,
        bucket: str,
        use_path_style: bool = True,
    ) -> None:
        import boto3
        from botocore.config import Config

        self._s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(s3={"addressing_style": "path" if use_path_style else "auto"}),
        )
        self._bucket = bucket
        # 确保 bucket 存在
        try:
            self._s3.head_bucket(Bucket=bucket)
        except Exception:
            self._s3.create_bucket(Bucket=bucket)

    @property
    def provider_name(self) -> str:
        return "s3"

    async def upload(self, object_key: str, data: bytes, content_type: str) -> str:
        self._s3.put_object(Bucket=self._bucket, Key=object_key, Body=data, ContentType=content_type)
        return object_key

    async def download(self, object_key: str) -> bytes:
        resp = self._s3.get_object(Bucket=self._bucket, Key=object_key)
        return resp["Body"].read()

    async def delete(self, object_key: str) -> bool:
        self._s3.delete_object(Bucket=self._bucket, Key=object_key)
        return True

    async def presigned_get_url(self, object_key: str, expires: int) -> str:
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": object_key},
            ExpiresIn=expires,
        )

    async def presigned_put_url(self, object_key: str, expires: int, content_type: str) -> str:
        return self._s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": object_key, "ContentType": content_type},
            ExpiresIn=expires,
            HttpMethod="PUT",
        )
