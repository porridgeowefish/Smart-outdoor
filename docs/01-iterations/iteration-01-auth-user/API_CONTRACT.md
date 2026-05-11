# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## POST /api/auth/register

用途：注册用户。

Request:

```json
{
  "username": "outdoor_user",
  "password": "plain_password",
  "nickname": "山野用户"
}
```

Response:

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

## POST /api/auth/login

用途：登录并获取 JWT。

Request:

```json
{
  "username": "outdoor_user",
  "password": "plain_password"
}
```

Response:

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

## GET /api/me

用途：获取当前用户资料。

要求：

```text
Authorization: Bearer jwt_token
```

## PATCH /api/me

用途：更新当前用户资料。

Request:

```json
{
  "nickname": "雪山徒步者",
  "avatar_url": "https://cdn.example.com/avatar.jpg"
}
```

规则：

```text
只允许更新 nickname / avatar_url
```
