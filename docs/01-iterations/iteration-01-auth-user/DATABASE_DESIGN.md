# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: ORM model and migrations when introduced.

## users

用途：保存用户身份、登录凭证和基础展示资料。

字段：

| 字段 | 说明 |
|---|---|
| id | 用户 ID |
| username | 登录名，唯一 |
| password_hash | 密码哈希，不能存明文 |
| nickname | 展示昵称 |
| avatar_url | 头像地址 |
| role | `user / admin` |
| status | `active / disabled` |
| created_at | 创建时间 |
| updated_at | 更新时间 |
| last_login_at | 最后登录时间 |

## 约束

```text
username 不能为空
password_hash 不能为空
username 唯一
role 默认 user
status 默认 active
```
