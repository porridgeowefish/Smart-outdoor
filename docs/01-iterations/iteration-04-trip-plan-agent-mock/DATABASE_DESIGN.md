# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: ORM model and migrations when introduced.

## trip_plans

保存一次规划任务的当前状态和压缩记忆。

关键字段：

```text
id
user_id
title
status
context_summary
context_state
created_at
updated_at
```

## trip_plan_messages

保存用户和 Agent 真实发生的对话消息。

关键字段：

```text
id
trip_plan_id
role
content
created_at
```

## agent_runs

保存每条用户消息触发的一次 Agent 后台运行。

关键字段：

```text
id
trip_plan_id
user_message_id
run_status
events_json
created_at
updated_at
```

## trip_plan_candidate_routes

保存 Agent 在某次规划中推荐过的候选线路。

关键字段：

```text
id
trip_plan_id
agent_run_id
route_asset_id
rank
advantage_tags
recommendation_reason
score_breakdown
planning_detail
evidence
created_at
```
