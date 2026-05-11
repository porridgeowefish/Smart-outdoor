# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## GET /api/trip-plans

用途：获取当前用户的 TripPlan 列表。

Response:

```json
{
  "items": [
    {
      "trip_plan_id": "tp_123",
      "title": "周末想从成都出发看雪山",
      "status": "draft",
      "context_summary": "用户想从成都出发看雪山",
      "updated_at": "2026-05-08T12:00:00+00:00"
    }
  ],
  "total": 1
}
```

## GET /api/trip-plans/{trip_plan_id}/messages

用途：读取某个 TripPlan 的会话历史和最近一次 AgentRun 的候选线路。

Response:

```json
{
  "trip_plan_id": "tp_123",
  "title": "周末想从成都出发看雪山",
  "status": "draft",
  "context_summary": "用户想从成都出发看雪山",
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "成都周边自驾一日徒步，中等强度",
      "created_at": "2026-05-08T12:00:00+00:00"
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "content": "我先给你筛出几条候选路线。",
      "created_at": "2026-05-08T12:00:01+00:00"
    }
  ],
  "candidate_routes": []
}
```

错误码：

```text
TRIP_PLAN_NOT_FOUND
```

## POST /api/trip-plans/messages

用途：发送用户消息，创建或继续规划对话。

Request:

```json
{
  "trip_plan_id": null,
  "content": "我周末想从成都出发，找一条能看雪山、一天往返的徒步路线"
}
```

当前实现不接受 `client_context`，请求模型 `extra=forbid`。

Response:

```json
{
  "trip_plan_id": "tp_123",
  "user_message_id": "msg_user_1",
  "assistant_message": {
    "id": "msg_assistant_1",
    "role": "assistant",
    "content": "还需要补充交通方式和强度偏好。",
    "created_at": "2026-05-08T12:00:01+00:00"
  },
  "agent_run_id": "run_789",
  "run_status": "waiting_user",
  "candidate_routes": []
}
```

信息充分时，`run_status` 为 `succeeded`。

`candidate_routes` 是本接口响应体中的字段，不是单独接口。当前实现由 Agent workflow 在本次 AgentRun 中同步生成，最多返回 3 条候选：

```json
{
  "candidate_id": "cand_1",
  "rank": 1,
  "route": {
    "route_id": "route_1",
    "name": "四姑娘山大峰",
    "location": "四川省 · 阿坝藏族羌族自治州",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "cover_image_url": null,
    "display_tags": ["雪山", "自驾友好"],
    "track_preview": {
      "format": "geojson",
      "coordinate_system": "wgs84",
      "point_count": 120,
      "geojson": {"type": "LineString", "coordinates": [[102.9, 31.0], [102.91, 31.01]]}
    }
  },
  "advantage_tags": ["综合匹配", "雪山", "一日友好"],
  "recommendation_reason": "线路距离和爬升适合作为候选评估。",
  "score_breakdown": {
    "total_score": 0.82,
    "ability_score": 0.8,
    "preference_score": 0.9,
    "metrics_score": 0.7,
    "evidence_score": 0.5,
    "matched_tags": ["雪山"],
    "route_tags": ["雪山", "中线"]
  }
}
```

错误码：

```text
TRIP_PLAN_NOT_FOUND
TRIP_PLAN_CLOSED
AGENT_ERROR
```

空消息当前由 Pydantic 校验返回 `422`，不是自定义 `EMPTY_MESSAGE`。

## GET /api/agent-runs/{agent_run_id}/events

用途：读取某次 AgentRun 的 SSE 事件流。

当前实现会从 `agent_runs.events_json` 重放已生成事件，响应 `Content-Type: text/event-stream`。

状态：

```text
backend implemented: event replay
frontend integration: pending
real streaming while workflow runs: pending
```

SSE 格式：

```text
event: run.phase_changed
data: {"phase":"route_retrieval"}

event: message.completed
data: {"content":"我先给你筛出几条候选路线。"}
```

事件类型：

```text
run.phase_changed
message.delta
message.completed
candidate_routes.updated
run.waiting_user
run.completed
```

当前实现没有主动生成 `run.failed` 事件；workflow 异常时 `POST /api/trip-plans/messages` 返回 `AGENT_ERROR`。

当前前端不依赖此接口渲染主流程。候选卡片主数据来自 `POST /api/trip-plans/messages` 响应体的 `candidate_routes`。

`candidate_routes.updated` 当前 payload:

```json
{
  "candidate_routes": [
    {
      "candidate_id": "cand_1",
      "rank": 1,
      "advantage_tags": ["综合匹配", "雪山"],
      "recommendation_reason": "线路距离和爬升适合作为候选评估。"
    }
  ]
}
```

错误码：

```text
AGENT_RUN_NOT_FOUND
```

## GET /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}

用途：查看候选线路在本次规划语境下的详情。

`candidate_id` 来自：

```text
POST /api/trip-plans/messages 响应中的 candidate_routes[].candidate_id
或
GET /api/trip-plans/{trip_plan_id}/messages 响应中的 candidate_routes[].candidate_id
```

Response:

```json
{
  "candidate_id": "cand_1",
  "rank": 1,
  "route": {
    "route_id": "route_1",
    "name": "四姑娘山大峰",
    "location": "四川省 · 阿坝藏族羌族自治州",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "cover_image_url": null,
    "display_tags": ["雪山", "自驾友好"],
    "track_preview": null
  },
  "advantage_tags": ["综合匹配", "雪山", "一日友好"],
  "recommendation_reason": "线路距离和爬升适合作为候选评估。",
  "score_breakdown": {},
  "planning_detail": {
    "summary": "这是一条可作为本次出行候选的线路。",
    "risk_notes": ["近期路况未确认，出发前需要再次核实。"],
    "estimated_duration": "约 5.8 小时"
  },
  "evidence": {
    "weather": {"status": "unconfirmed"},
    "transport": {"status": "unconfirmed"},
    "web_evidence": {"status": "unconfirmed"},
    "evaluator": {
      "passed": true,
      "issues": [],
      "warnings": []
    }
  }
}
```

当前响应不包含 `trip_plan_id` 和 `actions`。

前端跳转：

```text
response.route.route_id 可用于跳转线路资产详情：
GET /api/routes/{route_id}
```

错误码：

```text
CANDIDATE_ROUTE_NOT_FOUND
```

设计边界：

```text
点击候选详情不创建 snapshot
候选详情基于当前 TripPlan 语境、线路摘要、planning_detail 和 evidence
候选详情里的 route.route_id 指向 route_asset，可进入线路本体详情
无 confirmed 证据时只能保守表达，不能断言近期路况或绝对安全
```

## Route Retrieval / Evidence 时序

当前 `POST /api/trip-plans/messages` 的候选生成顺序：

```text
1. LLM 抽取 / 合并 context_state
2. 判断信息充分度
3. 从数据库可见 route_assets 召回线路
4. 按 ability / preference / metrics / 固定 evidence_score 排序
5. 取 top 3
6. 对 top 3 查询天气 / 交通 / Web 证据
7. 写入 trip_plan_candidate_routes
8. 返回 response.candidate_routes 给前端渲染候选卡片
```

当前限制：

```text
LLM 不直接生成路线。
天气 / 交通 / Web 证据查询发生在 top 3 之后。
真实证据当前不参与召回排序。
candidate_routes 概览数据来自 POST /api/trip-plans/messages 响应体。
SSE 的 candidate_routes.updated 当前不是完整卡片数据来源。
```
