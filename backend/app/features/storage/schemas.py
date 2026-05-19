from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StorageObjectMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_key: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=500)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    content_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(ge=0)


class ImageAssetMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_provider: str = Field(min_length=1, max_length=32)
    storage_key: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=500)
    original_filename: str | None = Field(default=None, max_length=255)
    processing_status: str = Field(default="ready", max_length=32)
    variants: dict[str, StorageObjectMetadata]


class UploadCredentialRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_type: str = Field(min_length=1, max_length=64)
    variant: str | None = Field(default=None, max_length=64)
    content_type: str = Field(min_length=1, max_length=120)
    original_filename: str = Field(min_length=1, max_length=255)
    size_bytes: int | None = Field(default=None, ge=0)


class UploadCredentialResponse(BaseModel):
    storage_provider: str
    storage_key: str
    upload_url: str
    public_url: str
    headers: dict[str, str]
    expires_at: datetime
