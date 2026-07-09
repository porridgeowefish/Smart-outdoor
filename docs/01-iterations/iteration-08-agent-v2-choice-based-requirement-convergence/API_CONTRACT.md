# API Contract

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic schemas and /openapi.json after implementation lands.

## 端点

| 方法 | 路径 | 本轮变化 |
|---|---|---|
| POST | `/api/trip-plans/messages` | 信息不足时响应返回结构化 `choice_request`；消息响应新增 `content_type` / `payload`；消息提交响应新增 `choice_request` / `confirmed_context` / `missing_fields` |
| POST | `/api/trip-plans/{trip_plan_id}/choice-results` | 新增端点：提交 `ask_user_choice` 的用户选择结果 |
| GET | `/api/trip-plans/{trip_plan_id}/messages` | 历史消息返回 `content_type` 和 `payload`，用于恢复选择卡 |

## 请求 / 响应示例

### POST /api/trip-plans/messages（信息不足）

Request:

```json
{
  "trip_plan_id": null,
  "content": "周末想出去走走，想看雪但别太危险"
}
```

Response（`run_status=waiting_user`）:

```json
{
  "trip_plan_id": "tp_123",
  "user_message_id": "msg_user_1",
  "assistant_message": {
    "id": "msg_assistant_1",
    "role": "assistant",
    "content": "我先确认几个关键偏好，这样推荐会更稳。",
    "content_type": "choice_request",
    "payload": {
      "tool_name": "ask_user_choice",
      "input": {
        "choice_request_id": "choice_req_123",
        "questions": []
      }
    },
    "created_at": "2026-05-20T12:00:01+00:00"
  },
  "agent_run_id": "run_789",
  "run_status": "waiting_user",
  "choice_request": {
    "choice_request_id": "choice_req_123",
    "questions": [
      {
        "type": "single_choice",
        "field": "transport_hint",
        "question": "这次交通更倾向哪种？",
        "header": "交通",
        "multi_select": false,
        "allow_custom": true,
        "options": [
          {"label": "自驾", "value": "self_drive", "description": "路线选择更灵活，但需要考虑停车和返程。"},
          {"label": "公共交通", "value": "public_transport", "description": "优先匹配公交或接驳更方便的路线。"},
          {"label": "都可以，帮我权衡", "value": "flexible", "description": "系统可以同时比较自驾和公共交通。"}
        ]
      }
    ]
  },
  "confirmed_context": {
    "items": [
      {"field": "departure_area", "label": "出发地", "value": "成都"},
      {"field": "activity_goal", "label": "目标", "value": "看雪"}
    ]
  },
  "missing_fields": ["transport_hint", "terrain_tolerance"],
  "candidate_routes": []
}
```

信息充分时：`run_status=succeeded`，`choice_request=null`，`candidate_routes` 返回最多 3 条候选。

### choice_request 结构

```json
{
  "choice_request_id": "choice_req_123",
  "questions": [
    {
      "type": "single_choice",
      "field": "transport_hint",
      "question": "这次交通更倾向哪种？",
      "header": "交通",
      "multi_select": false,
      "allow_custom": true,
      "options": [
        {"label": "自驾", "value": "self_drive", "description": "可选说明。"}
      ]
    }
  ]
}
```

choice_request 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| choice_request_id | str | 是 | 独立 UUID，提交答案时回指 |
| questions | array[ChoiceQuestion] | 是 | 1-3 个问题 |

ChoiceQuestion 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| type | `"single_choice"` \| `"multi_choice"` \| `"text"` | 是 | 问题类型 |
| field | str | 是 | 绑定的需求字段名 |
| question | str | 是 | 展示给用户的完整问题 |
| header | str | 是 | 短标签 |
| options | array[ChoiceOption] | 否 | 选项题提供 2-4 个；text 题为空数组 |
| multi_select | bool | 否 | 是否允许多选，默认 false |
| allow_custom | bool | 否 | 是否允许自定义输入，默认 true |

ChoiceOption 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| label | str | 是 | 展示文案 |
| value | str | 是 | 业务值 |
| description | str \| null | 否 | 选项说明 |

### POST /api/trip-plans/{trip_plan_id}/choice-results

用途：提交 `ask_user_choice` 的用户选择或自定义输入。

Request:

```json
{
  "choice_request_id": "choice_req_123",
  "answers": [
    {"field": "transport_hint", "value": "self_drive", "label": "自驾", "custom_text": null},
    {"field": "terrain_tolerance", "value": "avoid_icy_road", "label": "尽量不要冰雪路", "custom_text": null}
  ]
}
```

Response（选择后仍不足，`run_status=waiting_user`）：返回与 POST /messages 相同结构，`choice_request` 为下一组问题，`candidate_routes=[]`。

Response（选择后足够，`run_status=succeeded`）:

```json
{
  "trip_plan_id": "tp_123",
  "user_message_id": "msg_user_choice_1",
  "assistant_message": {
    "id": "msg_assistant_2",
    "role": "assistant",
    "content": "收到，我会按自驾、尽量避开冰雪路来收敛推荐。",
    "content_type": "text",
    "payload": null,
    "created_at": "2026-05-20T12:00:20+00:00"
  },
  "agent_run_id": "run_790",
  "run_status": "succeeded",
  "choice_request": null,
  "confirmed_context": {
    "items": [
      {"field": "departure_area", "label": "出发地", "value": "成都"},
      {"field": "activity_goal", "label": "目标", "value": "看雪"},
      {"field": "transport_hint", "label": "交通", "value": "自驾"},
      {"field": "terrain_tolerance", "label": "路况接受度", "value": "尽量避开冰雪路"}
    ]
  },
  "missing_fields": [],
  "candidate_routes": [
    {
      "candidate_id": "cand_1",
      "rank": 1,
      "route": {
        "route_id": "route_1",
        "name": "示例线路",
        "location": "四川省",
        "distance_km": 12.0,
        "elevation_gain_m": 650.0,
        "cover_image_url": null,
        "display_tags": ["雪景"],
        "track_preview": null
      },
      "advantage_tags": ["匹配偏好"],
      "recommendation_reason": "示例推荐理由。",
      "score_breakdown": {}
    }
  ]
}
```

ChoiceResultRequest 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| choice_request_id | str | 是 | 回指本次 choice_request |
| answers | array[ChoiceAnswer] | 是 | 至少 1 条；须覆盖本次全部 questions |

ChoiceAnswer 字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| field | str | 是 | 回答的字段名 |
| value | str \| array[str] | 是 | 单选为 str，多选为 array[str] |
| label | str \| array[str] | 是 | 与 value 对应的展示文案 |
| custom_text | str \| null | 否 | 自定义输入文本 |

### GET /api/trip-plans/{trip_plan_id}/messages 增量

每条消息返回 `content_type`（`text` / `choice_request` / `choice_result`）和 `payload`。前端据 assistant 消息的 `choice_request` payload 恢复选择卡，据 user 消息的 `choice_result` payload 恢复选择记录。

## 状态枚举

```text
agent_runs.run_status: running | waiting_user | succeeded | failed
trip_plan_messages.content_type: text | choice_request | choice_result
```

## 错误码

| HTTP | code | 触发 |
|---|---|---|
| 400 | TRIP_PLAN_CLOSED | TripPlan 已关闭，拒绝消息或选择提交 |
| 400 | INVALID_CHOICE_RESULT | field 不在白名单 / value 不在 options 且未 allow_custom / multi_select 与 value 类型不匹配 / answers 未覆盖全部 questions |
| 404 | TRIP_PLAN_NOT_FOUND | TripPlan 不存在或不属于当前用户 |
| 404 | CHOICE_REQUEST_NOT_FOUND | choice_request_id 不存在或不属于当前用户 / TripPlan |
| 409 | CHOICE_REQUEST_NOT_ACTIVE | choice_request 非 active（旧 / 已答 / 被替代） |
| 500 | AGENT_ERROR | Agent workflow 异常 |

## 历史来源

- DATABASE_DESIGN.md（context_state 字段白名单、content_type / payload 落库）
- TEST_PLAN.md（选择写入与失败路径用例）
- ../iteration-09-tag-knowledge-base-rag-choice-cards/API_CONTRACT.md（iter09 在本轮契约上做的增量）
