import asyncio
from pathlib import Path
from typing import Protocol

from botocore.config import Config
from botocore.exceptions import ClientError
import boto3

from app.config.settings import Settings, settings


class StorageConfigurationError(RuntimeError):
    pass


class DocumentStorage(Protocol):
    async def save_document(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> None:
        pass

    async def read_document(self, filename: str) -> bytes:
        pass

    async def delete_document(self, filename: str) -> None:
        pass

    async def document_exists(self, filename: str) -> bool:
        pass


class LocalDocumentStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    async def save_document(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> None:
        path = self._path(filename)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, content)

    async def read_document(self, filename: str) -> bytes:
        path = self._path(filename)
        if not path.exists():
            raise FileNotFoundError(filename)
        return await asyncio.to_thread(path.read_bytes)

    async def delete_document(self, filename: str) -> None:
        path = self._path(filename)
        if path.exists() and path.is_file():
            await asyncio.to_thread(path.unlink)

    async def document_exists(self, filename: str) -> bool:
        return await asyncio.to_thread(self._path(filename).is_file)

    def _path(self, filename: str) -> Path:
        return self.base_dir / Path(filename).name


class S3DocumentStorage:
    def __init__(self, config: Settings, *, require_endpoint: bool = False) -> None:
        if not config.storage_bucket:
            raise StorageConfigurationError("STORAGE_BUCKET is required")
        if require_endpoint and not config.storage_endpoint_url:
            raise StorageConfigurationError("STORAGE_ENDPOINT_URL is required for MinIO")

        client_kwargs = {
            "service_name": "s3",
            "region_name": config.storage_region,
            "endpoint_url": config.storage_endpoint_url,
            "config": Config(
                s3={"addressing_style": config.storage_addressing_style},
            ),
        }
        if config.storage_access_key_id and config.storage_secret_access_key:
            client_kwargs["aws_access_key_id"] = config.storage_access_key_id
            client_kwargs["aws_secret_access_key"] = config.storage_secret_access_key

        self.bucket = config.storage_bucket
        self.client = boto3.client(**client_kwargs)

    async def save_document(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> None:
        kwargs = {
            "Bucket": self.bucket,
            "Key": self._object_key(filename),
            "Body": content,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        await asyncio.to_thread(self.client.put_object, **kwargs)

    async def read_document(self, filename: str) -> bytes:
        def read() -> bytes:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=self._object_key(filename),
            )
            return response["Body"].read()

        try:
            return await asyncio.to_thread(read)
        except ClientError as exc:
            if _is_not_found(exc):
                raise FileNotFoundError(filename) from exc
            raise

    async def delete_document(self, filename: str) -> None:
        await asyncio.to_thread(
            self.client.delete_object,
            Bucket=self.bucket,
            Key=self._object_key(filename),
        )

    async def document_exists(self, filename: str) -> bool:
        try:
            await asyncio.to_thread(
                self.client.head_object,
                Bucket=self.bucket,
                Key=self._object_key(filename),
            )
            return True
        except ClientError as exc:
            if _is_not_found(exc):
                return False
            raise

    def _object_key(self, filename: str) -> str:
        return f"documents/{Path(filename).name}"


def create_document_storage(config: Settings = settings) -> DocumentStorage:
    backend = config.storage_backend.lower()
    if backend == "local":
        return LocalDocumentStorage(config.storage_local_dir)
    if backend == "s3":
        return S3DocumentStorage(config)
    if backend == "minio":
        return S3DocumentStorage(config, require_endpoint=True)
    raise StorageConfigurationError(
        "STORAGE_BACKEND must be one of: local, s3, minio"
    )


def _is_not_found(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code")
    return code in {"404", "NoSuchKey", "NotFound"}
