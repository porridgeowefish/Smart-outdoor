# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: this iteration plus Pydantic schemas and OpenAPI after implementation lands.

## 对齐结论

本轮采用双入口：

```text
POST /api/trip-plans/messages
用于提交自然语言用户消息，保持 Iteration 04 已有入口。

POST /api/trip-plans/{trip_plan_id}/choice-results
用于提交 ask_user_choice 工具调用的用户选择结果。
```

选择结果不伪装成普通自然语言文本。后端应把选择结果作为结构化 tool result 直接写入 `trip_plans.context_state`，同时生成可读的用户消息用于会话展示和审计。

选择结果是最高可信的用户确认事实，用来替代对应字段上的 AI 倾向判断。AI 从自然语言抽取出的字段只能作为低置信度草稿；当用户通过选择题确认某个字段后，后续 AI 抽取不能静默覆盖该字段。

## ask_user_choice 工具输入草案

Agent 在 workflow 中需要用户补充信息时，产出如下结构。该结构会进入接口响应的 `choice_request` 字段，也会作为 assistant message 的结构化 payload 落库。

```json
{
  "tool_name": "ask_user_choice",
  "input": {
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
          {
            "label": "自驾",
            "value": "self_drive",
            "description": "路线选择更灵活，但需要考虑停车和返程。"
          },
          {
            "label": "公共交通",
            "value": "public_transport",
            "description": "优先匹配公交或接驳更方便的路线。"
          },
          {
            "label": "都可以，帮我权衡",
            "value": "flexible",
            "description": "系统可以同时比较自驾和公共交通。"
          }
        ]
      },
      {
        "type": "text",
        "field": "departure_area",
        "question": "这次从哪里出发？",
        "header": "出发地",
        "multi_select": false,
        "allow_custom": true,
        "options": []
      }
    ]
  }
}
```

字段约束草案：

```text
choice_request_id: 本次选择请求 ID，用于提交答案时回指。
questions: 1-3 个问题。
前端必须逐步呈现问题，使用单题翻页或局部卡片平移，不一次性全部铺开。
type: single_choice | multi_choice | text。
field: 绑定 context_state 的字段名。
question: 展示给用户的完整问题。
header: 短标签，建议不超过 12 个中文字符。
options: 选项型问题提供 2-4 个选项；text 问题可为空数组。
multi_select: 是否允许多选。
allow_custom: 是否允许用户输入自定义内容。
```

## POST /api/trip-plans/messages

用途：提交自然语言消息，创建或继续 TripPlan。

Request:

```json
{
  "trip_plan_id": null,
  "content": "周末想出去走走，想看雪但别太危险"
}
```

Response:

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
    "questions": []
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

信息充分时：

```text
run_status=succeeded
choice_request=null
candidate_routes 返回最多 3 条候选
```

## 响应 Schema 增量草案

`TripPlanMessageResponse` 在现有字段基础上新增：

```json
{
  "id": "msg_1",
  "role": "assistant",
  "content": "我先确认几个关键偏好。",
  "content_type": "choice_request",
  "payload": {},
  "created_at": "2026-05-20T12:00:01+00:00"
}
```

`TripPlanMessagePostResponse` 在现有字段基础上新增：

```json
{
  "choice_request": null,
  "confirmed_context": {
    "items": []
  },
  "missing_fields": []
}
```

`choice_request_id` 使用独立 UUID，不复用 assistant message id。

`choice_request` 为 null 或：

```json
{
  "choice_request_id": "choice_req_123",
  "questions": []
}
```

## POST /api/trip-plans/{trip_plan_id}/choice-results

用途：提交 `ask_user_choice` 的用户选择或自定义输入。

Request:

```json
{
  "choice_request_id": "choice_req_123",
  "answers": [
    {
      "field": "transport_hint",
      "value": "self_drive",
      "label": "自驾",
      "custom_text": null
    },
    {
      "field": "terrain_tolerance",
      "value": "avoid_icy_road",
      "label": "尽量不要冰雪路，只看远处雪景",
      "custom_text": null
    }
  ]
}
```

Response:

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

如果选择后仍不足以推荐：

```text
run_status=waiting_user
choice_request 返回下一组选择问题
candidate_routes=[]
```

## ask_user_choice 工具返回草案

用户选择或输入后，宿主 UI 把结果通过 `POST /api/trip-plans/{trip_plan_id}/choice-results` 返回给 Agent：

```json
{
  "tool_name": "ask_user_choice",
  "result": {
    "answers": [
      {
        "field": "transport_preference",
        "value": "self_drive",
        "label": "自驾",
        "custom_text": null
      }
    ]
  }
}
```

自定义输入示例：

```json
{
  "tool_name": "ask_user_choice",
  "result": {
    "answers": [
      {
        "field": "transport_preference",
        "value": "chartered_bus_with_friends",
        "label": "包车和朋友一起去",
        "custom_text": "包车和朋友一起去"
      }
    ]
  }
}
```

多选示例：

```json
{
  "tool_name": "ask_user_choice",
  "result": {
    "answers": [
      {
        "field": "scenery_preferences",
        "value": ["snow_view", "forest", "open_ridge"],
        "label": ["雪景", "森林", "开阔山脊"],
        "custom_text": null
      }
    ]
  }
}
```

处理规则草案：

```text
后端校验 choice_request_id 是否属于当前用户和当前 trip_plan。
后端校验 field 是否属于允许写入的 context_state 字段。
后端校验 value 是否来自 options；allow_custom=true 时允许自定义文本。
后端把选择结果写入 trip_plan_messages，role=user，content_type=choice_result。
后端把答案直接写入 trip_plan.context_state，并标记该字段来源为 user_choice。
若同一字段已有 AI 抽取值，user_choice 覆盖 AI 抽取值。
若同一字段已有 user_choice 值，只有新的 choice_result 或用户自然语言明确修改才能覆盖。
合并后运行 sufficiency_check。
若条件不足，继续生成 ask_user_choice。
若条件足够，进入线路召回。
```

## GET /api/trip-plans/{trip_plan_id}/messages 增量

```text
返回 messages 时需要包含 content_type 和 payload。
前端根据 assistant message 的 choice_request payload 恢复选择栏。
前端根据 user message 的 choice_result payload 恢复用户选择记录。
历史会话恢复时，最近一次未完成 choice_request 仍可继续提交。
candidate_routes 仍表示最近一次 AgentRun 的候选线路。
```

## 状态枚举草案

```text
agent_runs.run_status:
- running
- waiting_user
- succeeded
- failed

trip_plan_messages.content_type:
- text
- choice_request
- choice_result
```

## 待对齐问题

```text
missing_fields 是否固定枚举。
场景化 sufficiency 规则的风险触发表。
```

## choice_request 活跃性与提交策略

本轮采用保守规则：

```text
不支持部分答案提交。
前端可以逐题呈现，但提交给后端时必须包含本次 choice_request 的全部问题答案。
后端按 trip_plan_messages 时间线判断 active choice_request，不设置 TTL。
只有当前 TripPlan 中最近一条未回答、未被新 choice_request 替代的 choice_request 可以提交。
旧 choice_request、已回答 choice_request 或被新 choice_request 替代的请求返回 CHOICE_REQUEST_NOT_ACTIVE。
CHOICE_REQUEST_NOT_ACTIVE 使用 HTTP 409。
choice_request_id 不存在、或不属于当前用户 / 当前 trip_plan 时返回 CHOICE_REQUEST_NOT_FOUND。
CHOICE_REQUEST_NOT_FOUND 使用 HTTP 404。
历史会话恢复时，只有最近一条 active choice_request 恢复为可交互选择卡。
已回答的 choice_request 只作为历史 assistant message 展示，不再允许提交。
```

## context_state 字段白名单

基础核心字段：

```text
activity_goal
departure_area
time_window
transport_hint
```

场景化阻塞字段：

```text
terrain_tolerance
safety_priority
```

说明：

```text
terrain_tolerance / safety_priority 默认不阻塞所有推荐。
当 activity_goal、preference_tags、avoid_tags 或用户原话涉及雪、冰雪路、野路、亲子、新手、安全优先等风险场景时，至少需要确认其中一个字段。
```

偏好字段：

```text
preference_tags
avoid_tags
scenery_preferences
supply_requirement
ability_hint
```

元字段：

```text
confirmed_fields
missing_fields
field_sources
```

字段来源：

```text
user_choice
user_explicit_text
ai_extracted
```

## 第一轮选择卡策略草案

第一轮选择卡不追求一次问完所有信息，而是优先补足推荐必需的核心字段。

核心字段控件策略：

```text
departure_area: text/custom 为主。
activity_goal: text/custom 为主。
time_window: text/custom 为主。
transport_hint: single_choice + custom。
```

偏好字段控件策略：

```text
偏好字段优先使用 single_choice 或 multi_choice。
每个偏好问题都应允许“其它/补充信息”，最终返回用户自定义文本，不把 Other 写成业务值。
```

当用户输入“周末想出去走走”这类短需求时，建议第一轮问题：

```text
departure_area: 从哪里出发？（text）
activity_goal: 这次想怎么走？（text）
time_window: 大概什么时候、几天？（text）
```

当自然语言已经包含部分核心字段时，只问缺失字段。例如“成都周末想看雪，但别太危险”：

```text
transport_hint: 交通更倾向哪种？
terrain_tolerance: 冰雪/野路接受程度？
safety_priority: 安全优先级是否高于风景和挑战？
```

一轮 `ask_user_choice` 最多 3 个问题，但前端逐步呈现：同一时间只突出一个问题，使用单题翻页或局部卡片平移。

问题优先级：

```text
1. departure_area
2. activity_goal
3. time_window
4. transport_hint
5. terrain_tolerance 或 safety_priority（风险场景触发）
6. scenery_preferences / preference_tags / avoid_tags
7. ability_hint（只作为用户偏好覆盖，不替代用户能力画像）
```

## sufficiency_check 规则

本轮采用场景化充分条件：

```text
基础充分条件：
- activity_goal 已确认
- departure_area 已确认
- time_window 已确认
- transport_hint 已确认

能力来源：
- 推荐匹配主要读取用户能力画像。
- ability_hint 只表达本次主观强度偏好或覆盖项，不作为默认基础核心字段。

风险场景加问：
- 如果目标、标签或原话涉及雪、冰雪路、野路、亲子、新手、安全优先等场景，需要确认 terrain_tolerance 或 safety_priority。
- 风险场景未确认时，不进入推荐，继续返回 ask_user_choice。
```

`confirmed_context` 返回可展示摘要，不返回完整内部 `context_state`：

```json
{
  "items": [
    {"field": "departure_area", "label": "出发地", "value": "成都"},
    {"field": "transport_hint", "label": "交通", "value": "自驾"}
  ]
}
```
