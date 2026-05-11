# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this iteration plus implemented tests.

## US-01.1 用户注册

作为新用户，我希望使用用户名注册账号，以便系统能够识别我是谁。

验收要点：

```text
username 必填且唯一
密码不能明文入库
重复用户名返回明确错误
注册成功返回用户基础信息
```

## US-01.2 用户登录

作为已注册用户，我希望使用用户名和密码登录，以便后续接口可以识别当前用户。

验收要点：

```text
使用 username + password 登录
密码错误返回失败
登录成功返回 access_token、token_type、user
后续请求使用 Authorization: Bearer token
```

## US-01.3 查看和更新个人资料

作为登录用户，我希望查看并更新昵称和头像，以便个人中心展示我的基础信息。

验收要点：

```text
GET /api/me 必须登录
PATCH /api/me 必须登录
PATCH /api/me 只允许更新 nickname / avatar_url
不能修改 role、status、password_hash
```
