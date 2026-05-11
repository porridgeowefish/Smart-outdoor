# Iteration 01 Auth + User

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户可以注册、登录、获取和更新自己的基础资料。

## 范围

接口：

```text
POST /api/auth/register
POST /api/auth/login
GET /api/me
PATCH /api/me
```

交付：

```text
JWT 登录
当前用户资料读取
昵称和头像更新
前端保存 token 并携带 Authorization
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`
- `docs/99-archive/backend-docs-legacy/US-02_PROFILE_AND_ABILITY_DESIGN.md`

## 本轮必补文档

```text
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

