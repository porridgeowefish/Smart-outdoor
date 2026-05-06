"""认证依赖注入：从请求头提取并验证 JWT Token，返回当前用户对象。

在 main.py 中注册为全局异常处理器，AuthError 会被统一转为 401 响应。"""

from __future__ import annotations

from fastapi import Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.features.users.model import User
from app.features.users.service import get_user_by_id


class AuthError(Exception):
    """认证失败异常，被 main.py 的全局 exception_handler 捕获并转为 401。"""
    pass


def unauthorized_response() -> JSONResponse:
    """返回标准化的 401 未认证响应。"""
    return JSONResponse(
        status_code=401,
        content={"code": "UNAUTHORIZED", "message": "未认证或登录已失效"},
    )


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI 依赖注入：从 Authorization 头解析 Bearer Token 并返回用户。

    校验链路：Token 格式 → JWT 签名 → 过期时间 → 用户存在 → 用户状态为 active。
    任一环节失败则抛出 AuthError。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if payload is None:
        raise AuthError
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise AuthError
    user = get_user_by_id(db, user_id)
    if user is None or user.status != "active":
        raise AuthError
    return user
