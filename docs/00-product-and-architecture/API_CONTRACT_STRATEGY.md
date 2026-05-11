# API 契约策略

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: Pydantic V2 schemas, FastAPI routes, and `/openapi.json`.

## 原则

本项目采用契约驱动前后端对接。

```text
后端 Pydantic V2 Request / Response
↓
FastAPI 自动生成 /openapi.json
↓
前端 openapi-typescript 生成类型
↓
统一 API client 调用
↓
mock response 也从 OpenAPI 类型派生
```

## 后端规则

```text
所有 Request / Response 使用 Pydantic V2 模型
业务层禁止传递裸 dict
错误码稳定
Response 必须匹配 OpenAPI
外部 API client 也应有 Pydantic 输入输出模型
```

## 前端规则

```text
禁止手写后端 Response 类型
禁止页面代码关心 mock / real
统一 apiClient
mock handler 使用生成类型约束
```

## Mock / Real 切换

后端：

```text
USE_MOCK_LLM=true
USE_MOCK_WEATHER=true
USE_MOCK_AMAP=true
USE_MOCK_SEARCH=true
```

前端：

```text
VITE_USE_MOCK_API=true
```

切换 mock/real 时只能改环境变量或 provider wiring，不允许改页面代码。

## Markdown API 文档定位

Markdown API 文档只解释：

```text
接口用途
业务规则
错误码
关键样例
验收重点
```

最终契约以 `/openapi.json` 和生成类型为准。

## 当前 API 归属

| 迭代 | API |
|---|---|
| 01 Auth + User | `/api/auth/register`, `/api/auth/login`, `/api/me` |
| 02 Route Upload + Parser | `/api/routes/upload` |
| 03 Route List + Detail | `/api/routes`, `/api/routes/{route_id}` |
| 04 TripPlan + Agent Mock | `/api/trip-plans/messages`, `/api/agent-runs/{id}/events`, candidate detail |
| 05 Snapshot / 我的规划 | save snapshot, snapshot list, snapshot detail |
| 06 Ability Profile | `/api/me/activity-tracks/upload`, `/api/me/ability-profile` |

