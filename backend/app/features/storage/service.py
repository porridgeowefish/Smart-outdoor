from __future__ import annotations

import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from app.core.config import get_settings


class InvalidStorageObjectError(Exception):
    """Storage metadata or key is not valid for the current user."""


class StorageObjectNotFoundError(Exception):
    """Requested storage object does not exist."""


class UnsupportedStorageProviderError(Exception):
    """Storage provider is not implemented in the current environment."""


@dataclass(frozen=True)
class StoredObject:
    provider: str
    key: str
    url: str
    content_type: str
    size_bytes: int


class StorageService:
    """Small storage boundary used by business services.

    The local provider writes to ASSET_STORAGE_DIR. COS credentials are exposed
    through the same contract, but real COS SDK signing is intentionally kept
    behind this boundary.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = _normalize_provider(self.settings.storage_provider)

    def put_bytes(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
        provider: str | None = None,
    ) -> StoredObject:
        provider_value = _normalize_provider(provider or self.provider)
        self._ensure_valid_key(key)
        if provider_value == "local":
            path = self._local_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return StoredObject(
                provider=provider_value,
                key=key,
                url=self.public_url(key, provider=provider_value),
                content_type=content_type,
                size_bytes=len(content),
            )
        client = self._cos_client()
        client.put_object(
            Bucket=self._cos_bucket(),
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return StoredObject(
            provider=provider_value,
            key=key,
            url=self.public_url(key, provider=provider_value),
            content_type=content_type,
            size_bytes=len(content),
        )

    def read_bytes(self, *, key: str, provider: str | None = None) -> bytes:
        provider_value = _normalize_provider(provider or self.provider)
        self._ensure_valid_key(key)
        if provider_value != "local":
            client = self._cos_client()
            try:
                response = client.get_object(Bucket=self._cos_bucket(), Key=key)
            except Exception as exc:
                raise StorageObjectNotFoundError from exc
            body = response.get("Body")
            if body is None:
                raise StorageObjectNotFoundError
            if hasattr(body, "get_raw_stream"):
                return body.get_raw_stream().read()
            if hasattr(body, "read"):
                return body.read()
            raise StorageObjectNotFoundError
        path = self._local_path(key)
        if not path.exists() or not path.is_file():
            raise StorageObjectNotFoundError
        return path.read_bytes()

    def public_url(self, key: str, *, provider: str | None = None) -> str:
        provider_value = _normalize_provider(provider or self.provider)
        self._ensure_valid_key(key)
        if provider_value == "local":
            base = self.settings.storage_public_base_url
            return f"{base}/{key}"
        base = (self.settings.cos_cdn_base_url or "").rstrip("/")
        if base:
            return f"{base}/{key}"
        bucket = self.settings.cos_bucket or "bucket"
        region = self.settings.cos_region or "region"
        return f"https://{bucket}.cos.{region}.myqcloud.com/{key}"

    def upload_url(self, key: str, *, provider: str | None = None) -> str:
        provider_value = _normalize_provider(provider or self.provider)
        self._ensure_valid_key(key)
        if provider_value == "local":
            return f"/api/storage/local-upload?key={key}"
        client = self._cos_client()
        return client.get_presigned_url(
            Method="PUT",
            Bucket=self._cos_bucket(),
            Key=key,
            Expired=15 * 60,
        )

    def download_url(
        self,
        key: str,
        *,
        provider: str | None = None,
        expires_seconds: int = 60 * 60,
    ) -> str:
        provider_value = _normalize_provider(provider or self.provider)
        self._ensure_valid_key(key)
        if provider_value == "local":
            return self.public_url(key, provider=provider_value)
        client = self._cos_client()
        return client.get_presigned_url(
            Method="GET",
            Bucket=self._cos_bucket(),
            Key=key,
            Expired=expires_seconds,
        )

    def delete_object(self, *, key: str, provider: str | None = None) -> None:
        provider_value = _normalize_provider(provider or self.provider)
        self._ensure_valid_key(key)
        if provider_value != "local":
            client = self._cos_client()
            client.delete_object(Bucket=self._cos_bucket(), Key=key)
            return
        path = self._local_path(key)
        if path.exists() and path.is_file():
            path.unlink()

    def _local_path(self, key: str) -> Path:
        return Path(self.settings.asset_storage_dir) / PurePosixPath(key)

    def _cos_bucket(self) -> str:
        if not self.settings.cos_bucket:
            raise UnsupportedStorageProviderError
        return self.settings.cos_bucket

    def _cos_client(self):
        if not (
            self.settings.cos_secret_id
            and self.settings.cos_secret_key
            and self.settings.cos_bucket
            and self.settings.cos_region
        ):
            raise UnsupportedStorageProviderError
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError as exc:
            raise UnsupportedStorageProviderError from exc

        config = CosConfig(
            Region=self.settings.cos_region,
            SecretId=self.settings.cos_secret_id,
            SecretKey=self.settings.cos_secret_key,
            Token=self.settings.cos_token,
            Scheme="https",
        )
        return CosS3Client(config)

    @staticmethod
    def _ensure_valid_key(key: str) -> None:
        path = PurePosixPath(key)
        if key.startswith("/") or ".." in path.parts or not key.strip():
            raise InvalidStorageObjectError


def get_storage_service() -> StorageService:
    return StorageService()


def build_upload_key(
    *,
    user_id: str,
    asset_type: str,
    variant: str | None,
    original_filename: str,
    content_type: str,
) -> str:
    extension = _extension_for(original_filename, content_type)
    token = uuid.uuid4().hex
    safe_variant = _safe_segment(variant or "file")
    if asset_type == "avatar":
        return f"users/{user_id}/avatar/{safe_variant}-{token}{extension}"
    if asset_type == "route_cover":
        return f"users/{user_id}/routes/covers/{safe_variant}-{token}{extension}"
    if asset_type == "route_track_raw":
        return f"users/{user_id}/routes/raw/{token}{extension}"
    if asset_type == "route_track_geojson":
        return f"users/{user_id}/routes/derived/{token}.geojson"
    raise InvalidStorageObjectError


def validate_key_for_user(*, key: str, user_id: str) -> None:
    StorageService._ensure_valid_key(key)
    if not key.startswith(f"users/{user_id}/"):
        raise InvalidStorageObjectError


def upload_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=15)


def _extension_for(filename: str, content_type: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension:
        return ".geojson" if extension == ".json" and content_type == "application/geo+json" else extension
    guessed = mimetypes.guess_extension(content_type)
    return guessed or ""


def _safe_segment(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum() or ch in {"-", "_"}) or "file"


def _normalize_provider(value: str) -> str:
    normalized = (value or "local").lower()
    if normalized == "object_storage":
        return "cos"
    return normalized
