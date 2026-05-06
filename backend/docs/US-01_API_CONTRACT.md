# US-01 API 契约：对话规划去哪

## 1. 设计边界

US-01 的主流程是：用户在“出去走走”通过自然语言表达出行需求，系统通过对话式 Agent 理解需求、必要时追问、推荐 3 条候选线路。用户点击候选卡片查看详情，确认有价值后可保存到“我的规划”。

本接口契约只覆盖 US-01 MVP 闭环：

1. 发送用户消息。
2. 订阅 AgentRun 流式事件。
3. 查看候选线路详情。
4. 保存候选为规划快照。
5. 获取我的规划列表。
6. 获取规划快照详情。

## 2. POST /api/trip-plans/messages

### 用途

用户发送一条对话消息。

如果请求中没有 `trip_plan_id`，后端创建新的 `trip_plan`，保存第一条用户消息，并创建一个 `agent_run`。

如果请求中有 `trip_plan_id`，后端向已有规划追加消息，并创建新的 `agent_run`。

### Request

```json
{
  "trip_plan_id": null,
  "content": "我周末想从成都出发，找一条能看雪山、一天往返的徒步路线",
  "client_context": {
    "timezone": "Asia/Shanghai",
    "locale": "zh-CN"
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---:|---:|---|
| trip_plan_id | string/null | 否 | 为空表示创建新规划；非空表示继续已有规划。 |
| content | string | 是 | 用户自然语言输入，不能为空。 |
| client_context.timezone | string | 否 | 客户端时区，用于把“明天、周末、早上”解析成明确时间。默认 `Asia/Shanghai`。 |
| client_context.locale | string | 否 | 客户端语言和格式偏好。默认 `zh-CN`。 |

### Response

```json
{
  "trip_plan_id": "tp_123",
  "message_id": "msg_456",
  "agent_run_id": "run_789",
  "run_status": "queued"
}
```

### 核心规则

1. 进入“出去走走”页面不创建 `trip_plan`。
2. 只有用户发送有效消息时才创建或更新 `trip_plan`。
3. 用户消息必须先落库，再创建 `agent_run`。
4. 每条用户消息触发一个新的 `agent_run`。
5. 如果 `trip_plan.status = closed`，不能继续追加消息。

### 错误码

```json
{"code":"EMPTY_MESSAGE","message":"消息内容不能为空"}
```

```json
{"code":"TRIP_PLAN_NOT_FOUND","message":"规划对话不存在"}
```

```json
{"code":"TRIP_PLAN_CLOSED","message":"该规划已结束，不能继续追加消息"}
```

## 3. GET /api/agent-runs/{agent_run_id}/events

### 用途

订阅某次 AgentRun 的实时事件流。该接口使用 SSE，不返回一次性 JSON。

### Response Header

```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### 统一事件外壳

```json
{
  "event_id": "evt_001",
  "agent_run_id": "run_789",
  "trip_plan_id": "tp_123",
  "type": "message.delta",
  "created_at": "2026-05-04T12:00:00Z",
  "payload": {}
}
```

### MVP 事件类型

| 事件类型 | 作用 |
|---|---|
| run.phase_changed | 展示 Agent 当前阶段。 |
| message.delta | 流式显示 Agent 文本。 |
| message.completed | Agent 文本消息完成。 |
| candidate_routes.updated | 渲染候选线路卡片。 |
| run.waiting_user | 展示 Agent 动态追问和选项。 |
| run.completed | AgentRun 成功结束。 |
| run.failed | AgentRun 失败。 |

### 事件示例

#### run.phase_changed

```json
{
  "type": "run.phase_changed",
  "payload": {
    "phase": "route_retrieval",
    "label": "正在检索候选线路"
  }
}
```

#### message.delta

```json
{
  "type": "message.delta",
  "payload": {
    "message_id": "msg_999",
    "delta": "成都周边一日往返看雪山，我会优先考虑交通时间、爬升强度和近期路况。"
  }
}
```

#### message.completed

```json
{
  "type": "message.completed",
  "payload": {
    "message_id": "msg_999",
    "content": "我先根据你的目标筛出 3 条候选路线。"
  }
}
```

#### candidate_routes.updated

```json
{
  "type": "candidate_routes.updated",
  "payload": {
    "candidates": [
      {
        "candidate_id": "cand_1",
        "route_id": "route_1",
        "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
        "name": "四姑娘山大峰",
        "distance_km": 15.2,
        "elevation_gain_m": 1320,
        "advantage_tags": ["雪山体验", "交通便利"]
      }
    ]
  }
}
```

#### run.waiting_user

`run.waiting_user` 是动态追问事件。Agent 决定问什么，协议规定怎么表达，前端只负责渲染。

```json
{
  "type": "run.waiting_user",
  "payload": {
    "question": "你更倾向自驾还是公共交通？",
    "options": [
      {"label": "自驾", "value": "self_drive"},
      {"label": "公共交通", "value": "public_transport"},
      {"label": "都可以", "value": "either"}
    ],
    "free_text_allowed": true,
    "context_key": "transport_hint"
  }
}
```

约束：

1. `question` 由 Agent 动态生成，但必须是明确问题。
2. `options` 由 Agent 动态生成，最多 3 个，可以为空。
3. `value` 是后端可解析的稳定短标识。
4. `free_text_allowed` 默认 true。
5. `context_key` 表示本次追问主要补齐哪个上下文字段。

#### run.completed

```json
{
  "type": "run.completed",
  "payload": {
    "final_message_id": "msg_999",
    "candidate_count": 3
  }
}
```

#### run.failed

```json
{
  "type": "run.failed",
  "payload": {
    "code": "ROUTE_RETRIEVAL_FAILED",
    "message": "线路检索失败，请稍后重试。",
    "recoverable": true
  }
}
```

### 前端规则

1. 收到 `run.completed` 后关闭 SSE。
2. 收到 `run.failed` 后关闭 SSE，并展示错误状态。
3. `message.delta` 用于流式文本。
4. `candidate_routes.updated` 用于聊天流中的线路卡片。
5. `run.waiting_user` 用于自然追问和可选选项。
6. SSE 只负责推送，不负责提交用户新消息。

## 4. GET /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}

### 用途

用户点击 Agent 推荐卡片后，查看该候选线路在本次规划语境下的详情。

点击卡片只查看详情，不创建 `route_plan_snapshot`。

### Response

```json
{
  "candidate_id": "cand_1",
  "trip_plan_id": "tp_123",
  "route": {
    "route_id": "route_1",
    "name": "四姑娘山大峰",
    "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "elevation_min_m": 3200,
    "elevation_max_m": 5025,
    "steep_ratio": 0.18,
    "climb_ratio": 86.8,
    "start_point": {"name":"海子沟入口","lon":102.9,"lat":31.0},
    "end_point": {"name":"海子沟入口","lon":102.9,"lat":31.0}
  },
  "planning_detail": {
    "fit_reason": "它适合你这次从成都出发、一日往返、想看雪山并接受一定挑战的需求。",
    "advantage_tags": ["雪山体验", "交通便利", "挑战感强"],
    "risk_notes": ["海拔较高，存在高反风险。", "爬升较大，不适合完全新手。"],
    "transport_plan": {"summary":"建议自驾前往，成都出发约 4-5 小时到达。","estimated_duration_minutes":270,"transport_mode":"self_drive"},
    "weather_summary": {"summary":"当前只展示规划生成时的天气判断，出发前需要刷新。","forecast_date":"2026-05-09","weather_text":"多云","temp_min_c":2,"temp_max_c":12},
    "budget_estimate": {"currency":"CNY","min_amount":300,"max_amount":600},
    "gear_suggestions": ["防风保暖层", "头灯", "登山杖"],
    "share_text": "我准备走四姑娘山大峰：约 15.2km，爬升 1320m，优势是雪山体验强、交通较方便。"
  },
  "evidence": [
    {"title":"近期路线记录或路况来源","url":"https://example.com","source_type":"web","summary":"用于说明近期是否有人实走或是否存在风险信息。","checked_at":"2026-05-04T12:00:00Z"}
  ],
  "actions": {
    "can_save_to_my_plans": true,
    "can_copy_share_text": true
  }
}
```

### 核心规则

1. 详情是 `RouteAsset + 本次 TripPlan 语境下的规划解释`。
2. 点击详情不创建 snapshot。
3. `evidence` 可为空，但字段保留。
4. `share_text` 可直接复制。
5. 用户点击“保存到我的规划”才创建 `route_plan_snapshot`。

## 5. POST /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save

### 用途

用户在候选详情页点击“保存到我的规划”，后端创建一个 `route_plan_snapshot`。

### Request

```json
{
  "note": "周末备选，适合约朋友一起走"
}
```

### Response

```json
{
  "snapshot_id": "snap_123",
  "trip_plan_id": "tp_123",
  "candidate_id": "cand_1",
  "route_id": "route_1",
  "saved_at": "2026-05-04T12:30:00Z"
}
```

### 核心规则

1. 一个 `trip_plan` 可以保存多个 snapshot。
2. 一个 `candidate_id` 最多生成一个 snapshot。
3. snapshot 保存当时生成的规划内容，不随未来线路资产变化自动变化。
4. 保存成功后，snapshot 出现在“我的规划”。
5. snapshot 不支持直接追问；继续追问应回到来源 `trip_plan`。

### 错误码

```json
{"code":"SNAPSHOT_ALREADY_EXISTS","message":"该候选线路已保存到我的规划"}
```

## 6. GET /api/my/route-plan-snapshots

### 用途

获取当前用户“我的规划”列表，展示用户保存过的 `route_plan_snapshot` 简介卡片。

### Query

| 参数 | 默认值 | 说明 |
|---|---:|---|
| page | 1 | 页码。 |
| page_size | 20 | 每页数量。 |
| status | 空 | MVP 可先不启用。 |
| keyword | 空 | 可按线路名称或备注搜索。 |

### Response

```json
{
  "items": [
    {
      "snapshot_id": "snap_123",
      "trip_plan_id": "tp_123",
      "route_id": "route_1",
      "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
      "name": "四姑娘山大峰",
      "distance_km": 15.2,
      "elevation_gain_m": 1320,
      "advantage_tags": ["雪山体验", "交通便利"],
      "saved_at": "2026-05-04T12:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### 核心规则

1. 我的规划展示 snapshot，不展示 trip_plan。
2. 一个 trip_plan 下保存的多个 snapshot，会显示为多张卡片。
3. 卡片样式应与“线路”区域卡片、Agent 推荐卡片保持一致。
4. 点击卡片进入 snapshot 详情。
5. snapshot 列表不支持直接追问。

## 7. GET /api/my/route-plan-snapshots/{snapshot_id}

### 用途

用户在“我的规划”点击某张规划卡片后，查看保存时刻的规划详情。

### Response

```json
{
  "snapshot_id": "snap_123",
  "trip_plan_id": "tp_123",
  "candidate_id": "cand_1",
  "route_id": "route_1",
  "route": {
    "name": "四姑娘山大峰",
    "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "elevation_min_m": 3200,
    "elevation_max_m": 5025,
    "start_point": {"name":"海子沟入口","lon":102.9,"lat":31.0},
    "end_point": {"name":"海子沟入口","lon":102.9,"lat":31.0}
  },
  "planning_detail": {
    "fit_reason": "适合你这次从成都出发、一日往返、想看雪山并接受一定挑战的需求。",
    "advantage_tags": ["雪山体验", "交通便利"],
    "risk_notes": ["海拔较高，存在高反风险。", "爬升较大，不适合完全新手。"],
    "transport_plan": {"summary":"建议自驾前往，成都出发约 4-5 小时到达。","estimated_duration_minutes":270,"transport_mode":"self_drive"},
    "weather_summary": {"summary":"保存时天气判断，仅供参考，出发前应刷新。","forecast_date":"2026-05-09","weather_text":"多云","temp_min_c":2,"temp_max_c":12},
    "budget_estimate": {"currency":"CNY","min_amount":300,"max_amount":600},
    "gear_suggestions": ["防风保暖层", "头灯", "登山杖"],
    "share_text": "我准备走四姑娘山大峰：约 15.2km，爬升 1320m。"
  },
  "evidence": [],
  "user_note": "周末备选，适合约朋友一起走",
  "saved_at": "2026-05-04T12:30:00Z",
  "actions": {
    "can_copy_share_text": true,
    "can_continue_conversation": true,
    "continue_trip_plan_id": "tp_123"
  }
}
```

### 核心规则

1. 返回保存时刻的快照内容。
2. 不自动重新查询天气、交通、路况。
3. 可以复制 `share_text`。
4. 可以跳回原 `trip_plan` 继续对话。
5. 不支持在 snapshot 内直接追问。
