# Database Design

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM model (`backend/app/features/trip_plans/model.py`) and migrations.

## 表

```text
新增 trip_plans
新增 trip_plan_messages
新增 agent_runs
新增 trip_plan_candidate_routes
复用 route_assets（routes 模块，候选来源）
复用 route_analysis_snapshots（routes 模块，召回前置条件）
复用 users（归属）
```

## trip_plans

保存一次规划任务的当前状态与压缩记忆。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str(36) | uuid | primary key | 新增 |
| user_id | str(36) | 用户 ID | index; foreign key: users.id | 新增 |
| title | str(120) | 规划标题 | 必填 | 新增 |
| status | str(32) | "draft" 等 | default "draft" | 新增 |
| context_summary | str\|null | Text | 压缩上下文摘要 | 新增 |
| context_state | dict | JSON | default dict；结构化上下文 | 新增 |
| created_at | datetime | tz-aware | server default (utcnow) | 新增 |
| updated_at | datetime | tz-aware | server default + onupdate | 新增 |

## trip_plan_messages

保存用户与 Agent 真实发生的对话消息。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str(36) | uuid | primary key | 新增 |
| trip_plan_id | str(36) | 规划 ID | index; foreign key: trip_plans.id | 新增 |
| role | str(32) | "user" / "assistant" | 必填 | 新增 |
| content | str | Text | 消息正文 | 新增 |
| content_type | str(32) | "text" / "choice_request" / "choice_result" | default "text" | 新增 |
| payload | dict\|null | JSON | choice_request / choice_result 承载 | 新增 |
| created_at | datetime | tz-aware | server default | 新增 |

## agent_runs

保存每条用户消息触发的一次 Agent 后台运行。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str(36) | uuid | primary key | 新增 |
| trip_plan_id | str(36) | 规划 ID | index; foreign key: trip_plans.id | 新增 |
| user_message_id | str(36) | 触发消息 ID | index; foreign key: trip_plan_messages.id | 新增 |
| run_status | str(32) | "running" / "waiting_user" / "succeeded" | default "running" | 新增 |
| events_json | array | JSON list[dict] | SSE 事件回放源；每项 {event:str, data:dict} | 新增 |
| created_at | datetime | tz-aware | server default | 新增 |
| updated_at | datetime | tz-aware | server default + onupdate | 新增 |

## trip_plan_candidate_routes

保存 Agent 在某次规划中推荐过的候选线路。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str(36) | uuid（对外即 candidate_id） | primary key | 新增 |
| trip_plan_id | str(36) | 规划 ID | index; foreign key: trip_plans.id | 新增 |
| agent_run_id | str(36) | 运行 ID | index; foreign key: agent_runs.id | 新增 |
| route_asset_id | str(36) | 线路资产 ID | index; 指向 route_assets.id | 新增 |
| rank | int | 1..3 | 召回排序位次 | 新增 |
| advantage_tags | array | JSON list[str] | 优势标签 | 新增 |
| recommendation_reason | str | Text | 推荐理由 | 新增 |
| score_breakdown | dict | JSON | 评分构成（ability/preference/metrics/evidence/matched/route_tags） | 新增 |
| planning_detail | dict | JSON | 规划细节（summary/risk_notes/estimated_duration 等） | 新增 |
| evidence | dict | JSON | 证据（weather/transport/web_evidence/evaluator） | 新增 |
| created_at | datetime | tz-aware | server default | 新增 |

## 约束

```text
候选线路必须来自数据库 route_assets，不能由 LLM 编造。
召回前置：route_assets.status = active；public 线路 + 本人 private 线路；必须存在 route_analysis_snapshot。
候选最多 3 条（workflow 切片 routes[:3]）。
evidence 查询只对 top 3 候选执行，不参与召回排序。
点击候选详情不创建 route_plan_snapshot（快照能力见后续迭代）。
```

## 迁移与同步点

```text
新增 trip_plans / trip_plan_messages / agent_runs / trip_plan_candidate_routes 表。
context_state 字段结构由后续迭代（iter08/iter09）扩展，本表定义保持稳定。
events_json 为 SSE 回放源；workflow 同步执行后写入，GET events 接口读取回放。
候选详情读取依赖 candidate_id（即 trip_plan_candidate_routes.id）。
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md`
- backend/app/features/trip_plans/model.py
- backend/app/features/routes/model.py（route_assets / route_analysis_snapshots）
