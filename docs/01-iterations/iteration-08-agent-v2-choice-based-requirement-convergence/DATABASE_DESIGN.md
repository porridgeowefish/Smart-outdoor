# Database Design

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM models and migrations after implementation lands.

## 表

```text
复用 trip_plans。
复用 trip_plan_messages（新增 content_type、payload 列）。
复用 agent_runs。
复用 trip_plan_candidate_routes。
不新增 choices 表：choice_request / choice_result 通过 trip_plan_messages.content_type + payload 表达。
```

## trip_plan_messages（本轮新增列）

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| content_type | str | `text` \| `choice_request` \| `choice_result` | default `text` | 新增 |
| payload | JSON \| null | 见下结构 | nullable | 新增 |

payload 结构：

```text
content_type=choice_request → {tool_name:str, input:{choice_request_id:str, questions:[ChoiceQuestion]}}
content_type=choice_result  → {choice_request_id:str, answers:[ChoiceAnswer]}
content_type=text           → null
```

## trip_plans.context_state（本轮白名单字段）

context_state 为 JSON 列。本轮 choice-results 只允许写入以下白名单（`CHOICE_WRITABLE_FIELDS`，见 `backend/app/features/trip_plans/context.py`）：

| 字段 | 类型 | 结构 / 取值 | 来源 | 本轮变化 |
|---|---|---|---|---|
| activity_goal | str | 活动目标文案 | choice/text | 复用 |
| departure_area | str | 出发地文案 | choice/text | 复用（iter09 升级为结构化） |
| time_window | object | `{raw_text:str, duration_days?:int}` | choice/text | 复用 |
| transport_hint | str | `self_drive` / `public_transport` / `flexible` 等 code | choice | 复用 |
| terrain_tolerance | str | `avoid_icy_road` / `accept_normal_trail` 等 code | choice | 复用 |
| safety_priority | str | `safety_first` / `balanced` 等 code | choice | 复用 |
| preference_tags | array[str] | 标签中文值 | choice | 复用 |
| avoid_tags | array[str] | 标签中文值 | choice | 复用 |
| scenery_preferences | array[str] | 风景英文键 | choice | 复用 |
| supply_requirement | str | `need_supply_points` 等 code | choice | 复用 |
| ability_hint | object | `{level:"beginner"\|"normal"\|"strong", raw_text?:str}` | choice | 复用（非基础核心字段） |

元字段（不由用户直接选择，由后端维护）：

| 字段 | 类型 | 结构 / 取值 | 来源 | 本轮变化 |
|---|---|---|---|---|
| confirmed_fields | array[str] | 已确认字段名 | server | 复用 |
| missing_fields | array[str] | 待确认字段名 | server | 复用 |
| field_sources | object | `{field: "user_choice"\|"user_explicit_text"\|"ai_extracted"}` | server | 复用 |

field_sources 样例：

```json
{
  "transport_hint": "user_choice",
  "activity_goal": "ai_extracted",
  "terrain_tolerance": "user_choice"
}
```

## 约束

```text
choice-results 只允许写入 CHOICE_WRITABLE_FIELDS 内的字段。
同字段来源优先级：user_choice > user_explicit_text > ai_extracted。
ai_extracted 不得静默覆盖已标为 user_choice 的字段。
选择式收敛阶段不写入 trip_plan_candidate_routes；只有 sufficiency_check 通过进入召回后才写入。
用户修改关键条件并重新召回时，新候选绑定新的 agent_run_id；历史候选不自动删除。
```

## 迁移与同步点

```text
trip_plan_messages 新增 content_type、payload 列；init_db 含 Iteration 08 兼容列补齐。
GET /api/trip-plans/{id}/messages 返回历史消息的 content_type 与 payload。
choice-results 写入后更新 trip_plans.context_state 并刷新 confirmed_fields / missing_fields / field_sources。
TripPlan 关闭（status=closed）时同时拒绝自然语言消息和 choice-results。
```

## 历史来源

- ../iteration-04-trip-plan-agent-mock/DATABASE_DESIGN.md（trip_plans / trip_plan_messages / agent_runs / candidate_routes 基线）
- ../iteration-06-ability-profile/README.md（ability_hint 与用户能力画像的边界）
- ../iteration-09-tag-knowledge-base-rag-choice-cards/DATABASE_DESIGN.md（iter09 在 context_state 上的字段增量）
