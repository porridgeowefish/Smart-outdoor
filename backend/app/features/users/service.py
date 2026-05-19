"""用户业务逻辑：查询用户、更新资料、上传头像。"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.features.users.model import User
from app.features.storage.service import InvalidStorageObjectError, validate_key_for_user
from app.features.users.schemas import UserUpdateRequest

_ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 头像大小上限 2MB


class InvalidAvatarFileError(Exception):
    """头像文件格式不支持或超过大小限制。"""
    pass


class InvalidAvatarMetadataError(Exception):
    """头像 metadata 不合法或不属于当前用户。"""
    pass


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """按主键查询用户。"""
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    """按用户名查询，用于登录和注册时的重复检查。"""
    return db.query(User).filter(User.username == username).first()


def update_user_profile(db: Session, user: User, data: UserUpdateRequest) -> User:
    """部分更新用户资料（仅修改请求中明确传入的字段）。"""
    update_data = data.model_dump(exclude_unset=True)
    if "nickname" in update_data:
        user.nickname = update_data["nickname"]
    if data.avatar is not None:
        _apply_avatar_metadata(user, data.avatar)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _apply_avatar_metadata(user: User, avatar) -> None:
    variants = avatar.variants
    display = variants.get("display")
    if display is None:
        raise InvalidAvatarMetadataError
    try:
        validate_key_for_user(key=avatar.storage_key, user_id=user.id)
        for variant in variants.values():
            validate_key_for_user(key=variant.storage_key, user_id=user.id)
    except InvalidStorageObjectError as exc:
        raise InvalidAvatarMetadataError from exc
    if avatar.storage_key != display.storage_key or avatar.url != display.url:
        raise InvalidAvatarMetadataError
    user.avatar_url = display.url
    user.avatar_storage_provider = avatar.storage_provider
    user.avatar_storage_key = display.storage_key
    user.avatar_variants = {
        key: value.model_dump() for key, value in variants.items()
    }
    user.avatar_original_filename = avatar.original_filename
    user.avatar_processing_status = avatar.processing_status


async def update_user_avatar(db: Session, user: User, file: UploadFile) -> User:
    """上传头像文件到本地存储目录，返回更新后的用户对象。

    文件按 {user_id}/{uuid}.{ext} 路径存储，通过 /static/avatars/ 暴露。
    """
    extension = _ALLOWED_AVATAR_TYPES.get(file.content_type or "")
    if extension is None:
        raise InvalidAvatarFileError

    content = await file.read()
    if not content or len(content) > _MAX_AVATAR_BYTES:
        raise InvalidAvatarFileError

    storage_root = Path(get_settings().avatar_storage_dir)
    user_dir = storage_root / user.id
    user_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = user_dir / filename
    file_path.write_bytes(content)

    user.avatar_url = f"/static/avatars/{user.id}/{filename}"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
