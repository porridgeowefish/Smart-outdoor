"""密码哈希与 JWT 工具模块。

密码使用 PBKDF2-HMAC-SHA256 存储（260000 次迭代），
JWT 使用手写 HS256 实现以避免引入 PyJWT 依赖。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings

_HASH_NAME = "sha256"
_ITERATIONS = 260_000  # OWASP 建议的 PBKDF2 迭代次数下限
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """对明文密码加盐哈希，返回格式为 `pbkdf2_sha256$iterations$salt$digest`。"""
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _HASH_NAME, password.encode("utf-8"), salt, _ITERATIONS
    )
    return (
        f"pbkdf2_{_HASH_NAME}${_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与存储的哈希是否匹配。使用 hmac.compare_digest 防止时序攻击。"""
    try:
        algorithm, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
        if algorithm != f"pbkdf2_{_HASH_NAME}":
            return False
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            _HASH_NAME, password.encode("utf-8"), salt, int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: str, role: str) -> str:
    """签发 JWT Access Token，payload 包含 sub（用户ID）、role 和 exp（过期时间戳）。"""
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": user_id, "role": role, "exp": int(expires_at.timestamp())}
    return _encode_jwt(payload, settings.jwt_secret_key)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """解码并验证 JWT Token。签名不合法或已过期时返回 None。"""
    settings = get_settings()
    payload = _decode_jwt(token, settings.jwt_secret_key)
    if payload is None:
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(datetime.now(timezone.utc).timestamp()):
        return None
    return payload


def _encode_jwt(payload: dict[str, Any], secret: str) -> str:
    """手写 JWT 编码：base64url(header).base64url(payload).base64url(signature)。"""
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        f"{_base64url_json(header)}.{_base64url_json(payload)}".encode("ascii")
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{signing_input.decode('ascii')}.{_base64url(signature)}"


def _decode_jwt(token: str, secret: str) -> dict[str, Any] | None:
    """手写 JWT 解码：验证签名后返回 payload 字典。"""
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected = hmac.new(
            secret.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()
        actual = _base64url_decode(signature_b64)
        if not hmac.compare_digest(actual, expected):
            return None
        header = json.loads(_base64url_decode(header_b64))
        if header.get("alg") != "HS256":
            return None
        return json.loads(_base64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _base64url_json(data: dict[str, Any]) -> str:
    """将 JSON 对象序列化为 base64url 编码字符串（无填充）。"""
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _base64url(raw)


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    """解码 base64url 字符串，自动补齐 padding。"""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))
