from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from app.features.storage.schemas import (
    UploadCredentialRequest,
    UploadCredentialResponse,
)
from app.features.storage.service import (
    InvalidStorageObjectError,
    UnsupportedStorageProviderError,
    build_upload_key,
    get_storage_service,
    upload_expires_at,
    validate_key_for_user,
)
from app.features.users.deps import get_current_user
from app.features.users.model import User

router = APIRouter(prefix="/storage", tags=["storage"])


@router.post("/upload-credentials", response_model=UploadCredentialResponse)
def create_upload_credentials(
    payload: UploadCredentialRequest,
    current_user: User = Depends(get_current_user),
) -> UploadCredentialResponse:
    try:
        key = build_upload_key(
            user_id=current_user.id,
            asset_type=payload.asset_type,
            variant=payload.variant,
            original_filename=payload.original_filename,
            content_type=payload.content_type,
        )
    except InvalidStorageObjectError:
        return JSONResponse(
            status_code=400,
            content={"code": "INVALID_STORAGE_OBJECT", "message": "Invalid storage object"},
        )
    storage = get_storage_service()
    try:
        return UploadCredentialResponse(
            storage_provider=storage.provider,
            storage_key=key,
            upload_url=storage.upload_url(key),
            public_url=storage.public_url(key),
            headers={"Content-Type": payload.content_type},
            expires_at=upload_expires_at(),
        )
    except UnsupportedStorageProviderError:
        return JSONResponse(
            status_code=503,
            content={
                "code": "STORAGE_PROVIDER_NOT_CONFIGURED",
                "message": "Storage provider is not configured",
            },
        )


@router.put("/local-upload")
async def local_upload(
    request: Request,
    key: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
):
    try:
        validate_key_for_user(key=key, user_id=current_user.id)
    except InvalidStorageObjectError:
        return JSONResponse(
            status_code=400,
            content={"code": "INVALID_STORAGE_OBJECT", "message": "Invalid storage object"},
        )
    content_type = request.headers.get("content-type", "application/octet-stream")
    content = await request.body()
    stored = get_storage_service().put_bytes(
        key=key,
        content=content,
        content_type=content_type,
        provider="local",
    )
    return {
        "storage_provider": stored.provider,
        "storage_key": stored.key,
        "url": stored.url,
        "content_type": stored.content_type,
        "size_bytes": stored.size_bytes,
    }
