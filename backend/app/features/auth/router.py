"""认证接口：用户注册和登录。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.features.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.features.auth.service import (
    DuplicateUserError,
    authenticate_user,
    create_user,
    mark_login_success,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户。用户名重复时返回 409。"""
    try:
        user = create_user(db, payload)
    except DuplicateUserError:
        return JSONResponse(
            status_code=409,
            content={"code": "USER_ALREADY_EXISTS", "message": "用户名已被使用"},
        )
    return RegisterResponse(user=user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """登录并签发 JWT Token。校验失败返回 401。"""
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        return JSONResponse(
            status_code=401,
            content={"code": "INVALID_CREDENTIALS", "message": "账号或密码错误"},
        )
    user = mark_login_success(db, user)
    return LoginResponse(
        access_token=create_access_token(user.id, user.role),
        token_type="bearer",
        user=user,
    )
