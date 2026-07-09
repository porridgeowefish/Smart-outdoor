# Database Design

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM model and migrations.

## 表

```text
新增 users。
```

## users

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str | UUID 字符串 | primary key，应用层生成 | 新增 |
| username | str | 登录名 | unique, not null | 新增 |
| password_hash | str | PBKDF2-HMAC-SHA256 哈希串 | not null；见 ORM model | 新增 |
| nickname | str | 展示昵称 | not null；未填时回填 username | 新增 |
| avatar_url | str\|null | 头像展示 URL | nullable | 新增 |
| avatar_storage_provider | str\|null | 对象存储 provider | nullable；iter07 复用 | 新增 |
| avatar_storage_key | str\|null | 对象存储 key | nullable；iter07 复用 | 新增 |
| avatar_variants | dict | 头像多规格信息 | JSON；iter07 复用 | 新增 |
| avatar_original_filename | str\|null | 头像原始文件名 | nullable；iter07 复用 | 新增 |
| avatar_processing_status | str\|null | 头像处理状态 | nullable；iter07 复用 | 新增 |
| role | str | `"user"` / `"admin"` | 默认 `"user"` | 新增 |
| status | str | `"active"` / `"disabled"` | 默认 `"active"` | 新增 |
| created_at | datetime | 创建时间 | server generated | 新增 |
| updated_at | datetime | 更新时间 | server generated，写入时刷新 | 新增 |
| last_login_at | datetime\|null | 最后登录时间 | nullable，登录成功时写入 | 新增 |

- 密码哈希算法与迭代次数见 ORM model（`security.py`）。
- `avatar_*` 系列字段在本轮建表时已预留，对象存储写入逻辑由 iter07 复用。

## 约束

```text
username 唯一且不能为空。
password_hash 不能为空，明文密码不入库。
role 默认 user。
status 默认 active。
并发注册同用户名时由唯一约束兜底（IntegrityError → USER_ALREADY_EXISTS）。
```

## 迁移与同步点

```text
新增 users 表。
密码写入路径须经过 hash_password；不得存明文。
登录路径须经过 verify_password。
last_login_at 在登录成功时由 mark_login_success 写入。
头像写入由 iter07 对象存储链路复用 avatar_* 字段。
```
