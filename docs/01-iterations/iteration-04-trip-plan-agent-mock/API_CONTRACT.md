# API Contract

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## 端点

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/trip-plans` | 当前用户的 TripPlan 列表 |
| GET | `/api/trip-plans/{trip_plan_id}/messages` | 某 TripPlan 的会话历史与最近一次 AgentRun 的候选 |
| POST | `/api/trip-plans/messages` | 发送用户消息，创建或继续规划对话 |
| GET | `/api/agent-runs/{agent_run_id}/events` | 某 AgentRun 的 SSE 事件流（回放） |
| GET | `/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}` | 候选线路在本次规划语境下的详情 |

`candidate_routes` 不是单独列表接口；它出现在 POST `/api/trip-plans/messages` 与 GET `/api/trip-plans/{trip_plan_id}/messages` 响应体中，分别表示本次 AgentRun 与最近一次 AgentRun 的候选线路。候选详情接口使用响应体中的 `candidate_id`。

## GET /api/trip-plans

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

Response:

```json
{
  "trip_plan_id": "tp_123",
  "title": "周末想从成都出发看雪山",
  "status": "draft",
  "context_summary": "用户想从成都出发看雪山",
  "messages": [
    {"id": "msg_1", "role": "user", "content": "成都周边自驾一日徒步，中等强度", "content_type": "text", "payload": null, "created_at": "2026-05-08T12:00:00+00:00"},
    {"id": "msg_2", "role": "assistant", "content": "我先给你筛出几条候选路线。", "content_type": "text", "payload": null, "created_at": "2026-05-08T12:00:01+00:00"}
  ],
  "candidate_routes": []
}
```

错误码:

```text
404 TRIP_PLAN_NOT_FOUND 不存在或不属于当前用户。
```

## POST /api/trip-plans/messages

用途：发送用户消息，创建或继续规划对话。workflow 在本次 AgentRun 中同步执行。

Request:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| content | str | 是 | min_length=1, max_length=2000；Request 模型 `extra=forbid` |
| trip_plan_id | str\|null | 否 | null / 缺失 → 新建 TripPlan；"tp_xxx" → 继续已有 TripPlan |

当前 Request `extra=forbid`，不接受 `client_context`。

Response（信息不足）:

```json
{
  "trip_plan_id": "tp_123",
  "user_message_id": "msg_user_1",
  "assistant_message": {"id": "msg_assistant_1", "role": "assistant", "content": "还需要补充交通方式和强度偏好。", "content_type": "text", "payload": null, "created_at": "2026-05-08T12:00:01+00:00"},
  "agent_run_id": "run_789",
  "run_status": "waiting_user",
  "choice_request": null,
  "confirmed_context": {"items": []},
  "missing_fields": [],
  "candidate_routes": []
}
```

Response（信息充分，`candidate_routes` 最多 3 条）:

```json
{
  "candidate_routes": [
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
        "track_preview": {"format": "geojson", "coordinate_system": "wgs84", "point_count": 120, "geojson": {"type": "LineString", "coordinates": [[102.9, 31.0], [102.91, 31.01]]}}
      },
      "advantage_tags": ["综合匹配", "雪山", "一日友好"],
      "recommendation_reason": "线路距离和爬升适合作为候选评估。",
      "score_breakdown": {"total_score": 0.82, "ability_score": 0.8, "preference_score": 0.9, "metrics_score": 0.7, "evidence_score": 0.5, "matched_tags": ["雪山"], "route_tags": ["雪山", "中线"]}
    }
  ]
}
```

`run_status` 取值：`running` / `waiting_user` / `succeeded`（见 service.py）。

错误码:

```text
404 TRIP_PLAN_NOT_FOUND trip_plan_id 不存在或不属于当前用户。
400 TRIP_PLAN_CLOSED 规划已关闭，不能追加。
500 AGENT_ERROR workflow 异常。
422 （Pydantic） 空 content 或 extra 字段；非自定义 EMPTY_MESSAGE。
```

## GET /api/agent-runs/{agent_run_id}/events

用途：读取某 AgentRun 的 SSE 事件流。当前从 `agent_runs.events_json` 重放已生成事件，`Content-Type: text/event-stream`。

SSE 格式:

```text
event: run.phase_changed
data: {"phase":"route_retrieval"}

event: message.completed
data: {"content":"我先给你筛出几条候选路线。"}
```

事件类型:

```text
run.phase_changed
message.delta
message.completed
candidate_routes.updated
run.waiting_user
run.completed
```

`candidate_routes.updated` payload（仅候选摘要，非完整卡片）:

```json
{
  "candidate_routes": [
    {"candidate_id": "cand_1", "rank": 1, "advantage_tags": ["综合匹配", "雪山"], "recommendation_reason": "线路距离和爬升适合作为候选评估。"}
  ]
}
```

错误码:

```text
404 AGENT_RUN_NOT_FOUND 不存在或不属于当前用户。
```

## GET /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}

用途：查看候选线路在本次规划语境下的详情。`candidate_id` 来自 messages 响应体。

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
    "evaluator": {"passed": true, "issues": [], "warnings": []}
  }
}
```

`response.route.route_id` 可用于跳转线路本体详情（`GET /api/routes/{route_id}`）。当前响应不含 `trip_plan_id` 与 `actions`。

错误码:

```text
404 CANDIDATE_ROUTE_NOT_FOUND 不存在或不属于当前用户 / TripPlan。
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/US-01_API_CONTRACT.md`
- DATABASE_DESIGN.md（context_state / events_json / 候选字段）
- workflow 时序与召回共识见 DELIVERY_NOTES.md
