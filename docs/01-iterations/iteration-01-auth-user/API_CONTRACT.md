# API Contract

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## 端点

| 方法 | 路径 | 本轮变化 |
|---|---|---|
| POST | `/api/auth/register` | 新增：用户注册 |
| POST | `/api/auth/login` | 新增：用户登录并签发 JWT |
| GET | `/api/me` | 新增：读取当前登录用户资料 |
| PATCH | `/api/me` | 新增：更新当前登录用户昵称 / 头像 |

## 请求 / 响应示例

### POST /api/auth/register

```json
{
  "username": "outdoor_user",
  "password": "plain_password",
  "nickname": "山野用户"
}
```

- `nickname` 为 Optional；未填时回填 `username`。
- 字段长度约束见 Schema（见 ORM/Schema），未知字段拒绝（extra=forbid）。

Response（201）：

```json
{
  "user": {
    "id": "user_123",
    "username": "outdoor_user",
    "nickname": "山野用户",
    "avatar_url": null,
    "role": "user"
  }
}
```

- `user` 为 `UserPublic`，不含密码相关字段。

### POST /api/auth/login

```json
{
  "username": "outdoor_user",
  "password": "plain_password"
}
```

Response（200）：

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "username": "outdoor_user",
    "nickname": "山野用户",
    "avatar_url": null,
    "role": "user"
  }
}
```

### GET /api/me

要求请求头 `Authorization: Bearer <jwt_token>`。

Response（200）：

```json
{
  "id": "user_123",
  "username": "outdoor_user",
  "nickname": "野用户",
  "avatar_url": null,
  "avatar_storage_provider": null,
  "avatar_storage_key": null,
  "avatar_variants": null,
  "avatar_processing_status": null,
  "role": "user",
  "status": "active",
  "created_at": "2026-01-01T00:00:00Z",
  "last_login_at": "2026-01-01T00:00:00Z"
}
```

### PATCH /api/me

要求请求头 `Authorization: Bearer <jwt_token>`。

```json
{
  "nickname": "雪山徒步者",
  "avatar": {
    "storage_provider": "local",
    "storage_key": "users/user_123/avatar/display.webp",
    "url": "/static/assets/users/user_123/avatar/display.webp",
    "original_filename": "avatar.jpg",
    "processing_status": "ready",
    "variants": {
      "display": {
        "storage_key": "users/user_123/avatar/display.webp",
        "url": "/static/assets/users/user_123/avatar/display.webp",
        "width": 512,
        "height": 512,
        "content_type": "image/webp",
        "size_bytes": 12
      },
      "thumbnail": {
        "storage_key": "users/user_123/avatar/thumbnail.webp",
        "url": "/static/assets/users/user_123/avatar/thumbnail.webp",
        "width": 128,
        "height": 128,
        "content_type": "image/webp",
        "size_bytes": 11
      }
    }
  }
}
```

- `nickname` 与 `avatar` 均 Optional，按请求传入字段部分更新。
- `avatar` 为 `ImageAssetMetadata`（见 ORM/Schema）；须先经 iter07 对象存储上传拿到 storage_key/url 后再提交。
- 字段白名单：仅允许更新 `nickname` / `avatar`；`extra=forbid`，多余字段返回 422。

Response：`UserMe`，结构同 GET /api/me。

## 错误码

| HTTP | code | 触发 |
|---|---|---|
| 409 | USER_ALREADY_EXISTS | 注册时用户名已被使用 |
| 401 | INVALID_CREDENTIALS | 登录账号或密码错误 |
| 401 | UNAUTHORIZED | 访问 /api/me 时未带、格式错、签名错、过期或用户非 active 的凭证 |
| 400 | INVALID_STORAGE_OBJECT | PATCH /api/me 提交的头像 metadata 不合法或不属于当前用户 |
| 422 | （FastAPI 校验） | 请求体字段缺失 / 超长 / 含白名单外字段（extra=forbid） |

## 历史来源

- [MVP_IMPLEMENTATION_SLICES.md](../../99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md)
- [US-01_API_CONTRACT.md](../../99-archive/backend-docs-legacy/US-01_API_CONTRACT.md)
- DATABASE_DESIGN.md
