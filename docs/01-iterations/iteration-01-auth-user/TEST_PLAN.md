# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: backend tests.

## API 测试

```text
注册成功
重复用户名失败
登录成功返回 JWT
密码错误失败
GET /api/me 无 token 失败
GET /api/me 有 token 成功
PATCH /api/me 成功修改 nickname / avatar_url
PATCH /api/me 不能修改 role/status
```

## Service 测试

```text
密码哈希不等于明文
verify_password 正确
账号查询支持 username
JWT payload 包含 sub / role / exp
```
