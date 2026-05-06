"""认证相关的请求/响应 Pydantic 模型。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.features.users.schemas import UserPublic


class RegisterRequest(BaseModel):
    """注册请求。nickname 未填时自动使用 username。"""
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    nickname: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def default_nickname(self) -> "RegisterRequest":
        """nickname 为空时回填 username，减少前端必填字段。"""
        if self.nickname is None:
            self.nickname = self.username
        return self


class RegisterResponse(BaseModel):
    user: UserPublic


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """登录成功响应，包含 JWT Token 和用户公开信息。"""
    access_token: str
    token_type: str
    user: UserPublic
