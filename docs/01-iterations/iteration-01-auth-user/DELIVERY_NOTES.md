# Delivery Notes

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation notes for this shipped iteration.

## 交付内容

- 注册 + 登录接口（POST /api/auth/register、POST /api/auth/login）。
- JWT 签发与校验（手写 HS256，payload 含 sub / role / exp）。
- PBKDF2-HMAC-SHA256 密码哈希与校验。
- 当前用户资料读取与更新（GET /api/me、PATCH /api/me）。
- users 表（含头像对象存储预留字段）。
- auth / 用户资料相关后端测试（backend/tests/auth/）。

> 本轮以全量 MVP 初始提交形式落地（git: `init: Smart_outdoor MVP 全量代码`），无独立迭代切片提交记录。

## 测试运行

```powershell
$env:DATABASE_URL='sqlite:///./test.db'; $env:JWT_SECRET_KEY='test-secret-key'; pytest backend/tests/auth
```

```text
历史迭代，未记录（测试已存在，未保留本轮历史运行计数）。
```

## 遗留风险

- 密码与 JWT 实现为手写（无 PyJWT / passlib 依赖）；轮换算法或多 audience 需自行扩展。
- 本轮无找回密码 / 改密码 / 账号禁用流程。
- 头像字段在本轮已预留 `avatar_*` 系列，但写入链路在 iter07 对象存储集成后才完整启用。
- 错误响应中 message 文案是否最终对前端稳定，未见本轮对齐记录。

## 对齐与决策

### 头像字段演进（iter07 复用）

- 本轮 users 表预留 avatar_url + avatar_storage_* + avatar_variants 字段。
- iter07 对象存储集成后，PATCH /api/me 的 avatar 由裸 URL 改为 `ImageAssetMetadata`（storage_key + variants）；本轮契约文档按当前已交付形态记录，未保留草案期的 `avatar_url: str` PATCH 形态。

## 暴露的权衡

- 手写 JWT（HS256）以避免引入 PyJWT 依赖；代价是缺少库提供的 audience / issuer / jti 等标准校验。
- 密码哈希固定 PBKDF2-SHA256（OWASP 下限迭代次数），未提供 argon2 等可选算法。
- 用户名密码为唯一登录方式，未预留手机号 / 邮箱 / 第三方登录的扩展位（schema 未对齐，后续迭代需评估）。
