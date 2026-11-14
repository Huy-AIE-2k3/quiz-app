"""Storage Service for S3 / Cloudflare R2 / MinIO object storage.

Handles:
- Uploading binary assets (put_object)
- Fetching assets (get_object)
- Deleting assets (delete_object)
- Copying assets on storage server (copy_object)
- Generating secure signed temporary URLs (generate_presigned_url)
- Verifying object existence (object_exists)
"""

import logging

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """S3-compatible Object Storage Client for assets and uploads."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        bucket_name: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region_name: str | None = None,
        use_mock: bool = False,
    ) -> None:
        self.use_mock = use_mock
        self._mock_storage: dict[str, tuple[bytes, str]] = {}

        if use_mock:
            self.endpoint_url = "http://mock-storage.local"
            self.bucket_name = "mock-bucket"
            self.client = None
            return

        settings = get_settings()
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT
        self.bucket_name = bucket_name or settings.S3_BUCKET
        self.access_key = access_key or settings.S3_ACCESS_KEY
        self.secret_key = secret_key or settings.S3_SECRET_KEY
        self.region_name = region_name or settings.S3_REGION

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            config=Config(signature_version="s3v4", s3={"addressing_style": "auto"}),
        )

    def put_object(
        self,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Uploads binary object bytes to S3/R2."""
        if self.use_mock or self.client is None:
            self._mock_storage[key] = (body, content_type)
            return

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType=content_type,
            )
        except ClientError as e:
            logger.error("Failed to upload object to S3 (%s): %s", key, e)
            raise

    def get_object(self, key: str) -> bytes:
        """Fetches object bytes from S3/R2."""
        if self.use_mock or self.client is None:
            if key not in self._mock_storage:
                raise FileNotFoundError(f"Key not found in mock storage: {key}")
            return self._mock_storage[key][0]

        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            logger.error("Failed to fetch object from S3 (%s): %s", key, e)
            raise

    def delete_object(self, key: str) -> None:
        """Deletes object from S3/R2."""
        if self.use_mock or self.client is None:
            self._mock_storage.pop(key, None)
            return

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            logger.warning("Failed to delete object from S3 (%s): %s", key, e)
            raise

    def copy_object(self, source_key: str, dest_key: str) -> None:
        """Copies an object directly on S3/R2 storage."""
        if self.use_mock or self.client is None:
            if source_key not in self._mock_storage:
                raise FileNotFoundError(f"Source key not found in mock storage: {source_key}")
            body, ctype = self._mock_storage[source_key]
            self._mock_storage[dest_key] = (body, ctype)
            return

        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_key}
            self.client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key,
            )
        except ClientError as e:
            logger.error("Failed to copy S3 object from %s to %s: %s", source_key, dest_key, e)
            raise

    def generate_presigned_url(self, key: str, expires_in: int = 21600) -> str:
        """Generates temporary presigned GET URL for secure downloading."""
        if self.use_mock or self.client is None:
            return f"https://mock-storage.local/{self.bucket_name}/{key}?expires_in={expires_in}"

        try:
            url = self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("Failed to generate presigned URL for %s: %s", key, e)
            raise

    def object_exists(self, key: str) -> bool:
        """Checks whether object exists in storage."""
        if self.use_mock or self.client is None:
            return key in self._mock_storage

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise


# Global default instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Returns singleton StorageService instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


def set_storage_service(service: StorageService | None) -> None:
    """Overrides singleton StorageService instance (useful for testing)."""
    global _storage_service
    _storage_service = service
