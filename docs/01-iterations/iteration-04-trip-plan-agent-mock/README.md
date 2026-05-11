# Iteration 04 TripPlan + Agent Workflow

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户在“出去走走”发送消息，系统创建或继续 trip_plan，建立 AgentRun，基于数据库线路资产召回候选，并返回可渲染的候选卡片。

## 范围

接口：

```text
GET /api/trip-plans
GET /api/trip-plans/{trip_plan_id}/messages
POST /api/trip-plans/messages
GET /api/agent-runs/{agent_run_id}/events
GET /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}
```

交付：

```text
第一条消息创建 trip_plan
后续消息追加到同一 trip_plan
每条用户消息创建 agent_run
closed trip_plan 禁止追加
消息接口同步执行 Agent workflow，直接返回 assistant_message / run_status / candidate_routes
TripPlan 列表和对话历史读取
SSE 后端事件回放已实现，但前端未接入，真实实时流式 pending
route_retrieval 从数据库可见线路中规则排序，最多返回 3 条候选
天气 / 交通 / Web 证据查询发生在 top 3 候选召回之后
当前 evidence 不参与路线排序，只进入 candidate detail / assistant 文案
候选详情返回 route + planning_detail + evidence
```

说明：

```text
candidate_routes 不是单独列表接口。
它出现在 POST /api/trip-plans/messages 响应中；
也出现在 GET /api/trip-plans/{trip_plan_id}/messages 响应中，表示最近一次 AgentRun 的候选线路。
候选详情接口使用其中的 candidate_id。
```

## SSE 当前状态

```text
已实现：
GET /api/agent-runs/{agent_run_id}/events
后端把 agent_runs.events_json 转成 text/event-stream 返回。

未完成：
前端尚未调用该接口。
当前不是边执行边推送，而是 workflow 完成后的事件回放。
candidate_routes.updated 不是候选卡片主数据来源。

当前前端主链路：
POST /api/trip-plans/messages 返回 assistant_message 和 candidate_routes。
```

## 当前召回共识

```text
真实 LLM
用于 context_state 抽取和 assistant 文案生成。

路线召回
不由 LLM 生成路线；后端从 route_assets + route_analysis_snapshots 规则召回和排序。

召回范围
route_assets.status = active
public 线路 + 当前用户自己的 private 线路
必须存在 route_analysis_snapshot

排序依据
ability_score + preference_score + metrics_score + 固定 evidence_score。

证据查询
天气 / 交通 / Web 搜索只对排序后的 top 3 候选执行。

当前限制
真实天气 / 交通 / Web 证据不参与排序，只用于详情 evidence、evaluator 和回复文案。
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`
- `docs/99-archive/backend-docs-legacy/US-01_API_CONTRACT.md`
- `docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md`
- `docs/99-archive/backend-docs-legacy/US-01_AGENT_WORKFLOW.md`

## 本轮必补文档

```text
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```
