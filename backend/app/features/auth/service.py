"""认证业务逻辑：用户创建、密码验证、登录记录。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.features.auth.schemas import RegisterRequest
from app.features.users.model import User
from app.features.users.service import get_user_by_username


class DuplicateUserError(Exception):
    """用户名已被注册。"""
    pass


def create_user(db: Session, payload: RegisterRequest) -> User:
    """创建新用户。先查询用户名是否已存在，再用 IntegrityError 兜底并发场景。"""
    if get_user_by_username(db, payload.username) is not None:
        raise DuplicateUserError

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname or payload.username,
        role="user",
        status="active",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # 并发注册时查询可能未命中但写入冲突，rollback 后抛出业务异常
        db.rollback()
        raise DuplicateUserError from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """校验用户名密码，成功返回 User 对象，失败返回 None。"""
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def mark_login_success(db: Session, user: User) -> User:
    """更新用户最后登录时间并持久化。"""
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
