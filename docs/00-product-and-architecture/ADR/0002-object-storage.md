# ADR-0002 Object Storage for Image Assets and Large Track Artifacts

Status: accepted
Date: 2026-06-14

## Context

> 回溯重建：本决策实际发生于 iteration-07（Object Storage + Image Assets）交付期间，原始 contemporaneous 决策记录缺失。本文据 iteration-07 迭代文档与已实现代码反推，部分 rationale 为推断。

iteration-07 需要为图片资产（线路封面、用户头像）和大型轨迹产物提供存储。在此之前的本地静态文件 / 后端代理上传方案在云部署下不可扩展：后端要承接大文件带宽与处理压力，且与云对象存储生态割裂。

来源：iteration-07 `USER_STORIES.md`、`DELIVERY_NOTES.md`。

## Decision

采用前端直传对象存储 + 后端签发临时凭据：

```text
- 上传：前端先请求后端签发临时凭据，再用 signed PUT URL 直传对象存储，后端不经手文件本体。
- Provider：主用腾讯云 COS；保留 local provider 作开发态 fallback；抽象层预留 OSS/S3/MinIO 切换点。
- 签名 URL：约 15 分钟过期。
- 访问控制：public-read bucket + Referer 白名单防盗链。
- 跨域：配置 CORS 支持浏览器 PUT/GET/HEAD 预检。
- 持久化：DB 只存 *_storage_provider + *_storage_key + variants 元数据，不存文件本体。
```

依据：`backend/app/features/storage/service.py`、`backend/app/core/config.py`、iteration-07 `DATABASE_DESIGN.md`。

## Consequences

收益：

```text
- 后端不经手大文件，带宽与 CPU 压力下降。
- 支持云部署的可扩展存储。
- Referer 防盗链保护图片资产。
```

代价：

```text
- CORS 配置负担：曾因缺失导致上线 403（见 iteration-07 INCIDENT_REPORT_2026-05-19_UPLOAD_CORS）。
- 密钥管理复杂度上升（COS 凭据进环境变量）。
- 云端验收必须同时覆盖上传（OPTIONS 预检 + 直传）与读取（防盗链）两条链路（见 agent-rules/70-object-storage.md）。
```

## Alternatives Considered

- 后端代理上传：放弃，后端承压且违背引入对象存储的初衷。
- 纯本地文件：仅保留为开发态 fallback，不作生产方案。
- 锁定单一云厂商：放弃，抽象层预留多 provider 以保留迁移空间。
