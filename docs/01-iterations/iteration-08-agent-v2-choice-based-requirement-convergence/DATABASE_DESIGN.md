# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: ORM model and migrations after implementation lands.

## 对齐结论

本轮复用 Iteration 04 的核心表：

```text
trip_plans
trip_plan_messages
agent_runs
trip_plan_candidate_routes
```

新增能力优先通过 `trip_plan_messages` 的结构化 payload 表达，不新增独立 choices 表，除非实现时发现查询或审计成本明显过高。

## trip_plans

继续保存一次规划任务的当前状态和压缩记忆。

新增或明确 `context_state` 字段语义：

```text
context_state 保存当前规划需求状态。
choice-result 是用户显式确认，直接写入 context_state。
choice-result 用来替代对应字段上的 AI 倾向判断。
自然语言 AI 抽取只能作为低置信度草稿写入 context_state。
choice-result 提交后，后端只允许写入白名单字段。
推荐生成后，context_state 不关闭；后续追问和修改继续基于它工作。
```

字段可信度优先级：

```text
user_choice > user_explicit_text > ai_extracted
```

覆盖规则：

```text
AI 抽取不得静默覆盖 user_choice 字段。
用户再次提交 choice-result 可以覆盖旧 user_choice。
用户自然语言明确修改时，可以覆盖 user_choice，但需要把来源标为 user_explicit_text。
```

本轮 `context_state` 白名单分层：

基础核心字段，直接影响是否可以进入推荐：

```text
activity_goal
departure_area
time_window
transport_hint
```

场景化阻塞字段，仅在风险场景下影响是否可以进入推荐：

```text
terrain_tolerance
safety_priority
```

偏好字段，影响选择卡、召回加权、扣分和解释，但不默认阻塞推荐：

```text
preference_tags
avoid_tags
scenery_preferences
supply_requirement
ability_hint
```

元字段，用于可信度、展示和调试：

```text
confirmed_fields
missing_fields
field_sources
```

暂不纳入本轮充分条件，但可由客户端或后续迭代补充：

```text
current_location
communication_requirement
emergency_requirement
budget_hint
group_profile
```

`field_sources` 记录每个字段的来源：

```json
{
  "transport_hint": "user_choice",
  "activity_goal": "ai_extracted",
  "terrain_tolerance": "user_choice"
}
```

字段结构草案：

```json
{
  "activity_goal": "看雪",
  "departure_area": "成都",
  "time_window": {
    "raw_text": "周末一天",
    "duration_days": 1
  },
  "transport_hint": "self_drive",
  "ability_hint": {
    "level": "normal",
    "raw_text": "这次想轻松一些",
    "meaning": "本次主观强度偏好，不替代用户能力画像"
  },
  "preference_tags": ["雪景", "森林"],
  "avoid_tags": ["冰雪路", "野路"],
  "terrain_tolerance": "avoid_icy_road",
  "scenery_preferences": ["snow_view", "forest"],
  "safety_priority": "high",
  "supply_requirement": "need_supply_points",
  "confirmed_fields": ["transport_hint", "terrain_tolerance"],
  "missing_fields": ["time_window"],
  "field_sources": {
    "activity_goal": "ai_extracted",
    "transport_hint": "user_choice",
    "terrain_tolerance": "user_choice"
  }
}
```

能力字段说明：

```text
用户能力画像是能力匹配的主要来源。
ability_hint 只记录本次对话里的主观强度偏好或覆盖说明。
ability_hint 不属于基础核心字段。
当用户表达“这次想轻松一点”时，可以写入 ability_hint，但不能据此改写用户长期能力画像。
```

## trip_plan_messages

当前字段：

```text
id
trip_plan_id
role
content
created_at
```

本轮建议新增：

```text
content_type
payload
```

字段语义：

```text
content_type=text
普通自然语言用户消息或普通 assistant 回复。

content_type=choice_request
assistant 通过 ask_user_choice 工具调用向用户提出选择问题。
payload 保存 tool_name、choice_request_id 和 questions。
content 保存可读摘要，用于降级展示。

content_type=choice_result
用户提交选择结果。
payload 保存 choice_request_id 和 answers。
content 保存用户可读的选择摘要，例如“选择：自驾；尽量不要冰雪路”。
```

## agent_runs

当前字段：

```text
id
trip_plan_id
user_message_id
run_status
events_json
created_at
updated_at
```

本轮状态语义：

```text
running: workflow 正在执行。
waiting_user: workflow 产出 ask_user_choice，需要用户选择后继续。
succeeded: 已完成本轮处理，可能返回候选推荐或普通回答。
failed: workflow 失败，接口返回错误并写入可追踪事件。
```

说明：

```text
HTTP 实现中不要求一个 AgentRun 长时间挂起等待前端。
当 run_status=waiting_user 时，本次 AgentRun 已落库并结束。
用户提交 choice-result 后创建新的 AgentRun，基于同一个 trip_plan.context_state 继续推进。
从产品视角看，会话状态没有停止，因为 TripPlan 和 context_state 持续存在。
```

## trip_plan_candidate_routes

沿用 Iteration 04 设计。

补充约束：

```text
选择式收敛阶段不写入 candidate_routes。
只有 sufficiency_check 通过并进入 route_retrieval 后才写入候选线路。
用户修改关键条件并重新召回时，新候选绑定新的 agent_run_id。
历史候选不自动删除；前端默认展示最近一次 AgentRun 的候选。
```
