# Test Plan

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: backend tests.

## Service / Unit

- [US-01.1] create_user 写入的 password_hash 不等于明文密码。
- [US-01.1] create_user 对已存在用户名抛 DuplicateUserError（含并发 IntegrityError 兜底）。
- [US-01.2] authenticate_user 用正确用户名 + 密码返回 User，密码错误返回 None。
- [US-01.2] verify_password 对正确密码返回 True、错误密码返回 False。
- [US-01.2] get_user_by_username 按用户名命中用户。
- [US-01.2] JWT payload 包含 sub（用户 ID）、role、exp，签名 / 过期校验生效。

## API

- [US-01.1] POST /api/auth/register 成功返回 201 与 UserPublic，响应体不含 password / password_hash。
- [US-01.1] POST /api/auth/register 重复用户名返回 409 USER_ALREADY_EXISTS。
- [US-01.1] POST /api/auth/register 缺 username 返回 422。
- [US-01.1] POST /api/auth/register 未填 nickname 时回填 username。
- [US-01.2] POST /api/auth/login 成功返回 access_token + token_type=bearer + user。
- [US-01.2] POST /api/auth/login 密码错误返回 401 INVALID_CREDENTIALS。
- [US-01.3] GET /api/me 带 Bearer token 返回当前用户资料。
- [US-01.3] PATCH /api/me 仅更新 nickname 后返回更新值，role/status 不变。
- [US-01.3] PATCH /api/me 含白名单外字段（如 role）返回 422。
- [US-01.3] PATCH /api/me 更新头像 metadata 后 avatar_url / avatar_storage_key 生效，GET /api/me 持久化。
- /openapi.json 暴露 /api/auth/register、/api/auth/login、/api/me 契约。

## 权限

- [US-01.3] GET /api/me 不带 token 返回 401 UNAUTHORIZED。
- [US-01.3] GET /api/me 带格式错 / 签名错 / 过期 token 返回 401 UNAUTHORIZED。
- [US-01.3] 用户状态非 active 时带其 token 访问 /api/me 返回 401。

## 失败路径

- [US-01.3] PATCH /api/me 提交不属于当前用户的头像 storage_key 返回 400 INVALID_STORAGE_OBJECT。
- [US-01.3] PATCH /api/me 提交非法头像 metadata（如缺 display 变体）返回 400 INVALID_STORAGE_OBJECT。

## 验证命令

```powershell
$env:DATABASE_URL='sqlite:///./test.db'; $env:JWT_SECRET_KEY='test-secret-key'; pytest backend/tests/auth
$env:DATABASE_URL='sqlite:///./test.db'; $env:JWT_SECRET_KEY='test-secret-key'; pytest backend/tests/auth/test_auth_api.py backend/tests/auth/test_auth_service.py
```

## 备注

- 头像相关失败路径依赖 iter07 对象存储链路；本轮用例覆盖触发 `INVALID_STORAGE_OBJECT` 的边界。
