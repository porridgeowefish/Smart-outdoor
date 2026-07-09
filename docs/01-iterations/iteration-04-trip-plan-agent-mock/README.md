# Iteration 04 TripPlan + Agent Workflow

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户在“出去走走”发送消息，系统创建或继续 trip_plan，建立 AgentRun，基于数据库线路资产召回候选，并返回可渲染的候选卡片。

## 本轮目标

```text
完成 TripPlan + Agent workflow 的最小可运行闭环。
用户发消息创建或继续规划对话，系统同步执行 workflow 并返回 assistant 文案与候选线路。
候选线路由后端从数据库可见 route_assets 规则召回排序，不由 LLM 编造。
天气 / 交通 / Web 证据查询只对 top 3 候选执行，用于详情与文案，不参与排序。
提供 SSE 事件回放接口（前端接入与真实边执行边推送留待后续）。
```

## 范围

### 本轮覆盖

```text
第一条消息创建 trip_plan，后续消息追加到同一 trip_plan。
每条用户消息创建一个 agent_run。
closed trip_plan 禁止追加。
消息接口同步执行 Agent workflow，直接返回 assistant_message / run_status / candidate_routes。
route_retrieval 从数据库可见线路（public + 本人 private，且须有 analysis snapshot）规则排序，最多 3 条候选。
证据（天气 / 交通 / Web）只对 top 3 候选查询，进入 candidate detail 与 assistant 文案。
TripPlan 列表、会话历史、候选详情读取。
GET /api/agent-runs/{agent_run_id}/events 从 events_json 回放 SSE。
```

### 暂不进入

```text
真实边执行边推送（当前 workflow 同步跑完再回放 events_json）。
前端 SSE 接入与流式体验。
evidence 参与召回排序（当前固定 evidence_score，真实证据不进排序）。
client_context 请求字段（当前 Request extra=forbid）。
新建独立对话接口（沿用 messages 合并接口 + trip_plan_id 区分新建/继续）。
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`
- `docs/99-archive/backend-docs-legacy/US-01_API_CONTRACT.md`
- `docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md`
- `docs/99-archive/backend-docs-legacy/US-01_AGENT_WORKFLOW.md`
