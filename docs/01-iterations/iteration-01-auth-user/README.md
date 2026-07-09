# Iteration 01 Auth + User

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户可以注册、登录、获取和更新自己的基础资料。

## 本轮目标

```text
用户用用户名注册账号并完成密码校验登录。
登录后签发 JWT，后续请求用 Authorization: Bearer 携带。
当前用户能读取自己的基础资料，并能更新昵称和头像。
```

## 范围

### 本轮覆盖

```text
用户注册（用户名 + 密码，密码不明文入库）。
用户名 + 密码登录并签发 JWT。
GET /api/me 读取当前登录用户资料。
PATCH /api/me 更新昵称和头像。
```

### 暂不进入

```text
不做手机号 / 邮箱注册与验证码登录。
不做第三方（微信 / Apple）登录。
不做找回密码、改密码、账号禁用流程。
不做角色权限管理（role 字段保留但不开放管理界面）。
不做活动轨迹、能力画像（属后续迭代）。
```

## 历史来源

- [MVP_IMPLEMENTATION_SLICES.md](../../99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md)
- [US-02_PROFILE_AND_ABILITY_DESIGN.md](../../99-archive/backend-docs-legacy/US-02_PROFILE_AND_ABILITY_DESIGN.md)
