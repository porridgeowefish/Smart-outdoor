# 80 运行配置与密钥

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: runtime configuration and secret handling rules.

## 运行配置唯一事实源

```text
backend/.env 是本地开发和云端部署的运行配置最高事实源。
本地开发：rebuilt.ps1 / rebuilt.cmd 读取 backend/.env，并按本地 PostgreSQL 覆盖 DATABASE_URL。
云端部署：deploy_cloud.py 读取本地 backend/.env，上传为远端 backend/.env。
容器编排：docker-compose.yml 的 backend 服务读取 ./backend/.env。
禁止恢复或手工维护 backend/.env.production 作为第二份运行配置。
部署脚本不得内置一套与 backend/.env 重复的 COS / LLM / 外部服务配置。
```

## 私有密钥

```text
docs/99-archive/backend-docs-legacy/PRIVATE_SECRETS.local.md 只允许本地使用。
不得在回复、提交信息、Issue、PR 或公开文档中展示真实密钥。
```
