# ADR-0003 Choice-based Requirement Convergence (Agent V2)

Status: accepted
Date: 2026-06-14

## Context

> 回溯重建：本决策实际发生于 iteration-08（Agent V2 Choice-based Requirement Convergence）交付期间，原始 contemporaneous 决策记录缺失。本文据 iteration-08 迭代文档与已实现代码反推，部分 rationale 为推断。

Agent V1 一次性从用户自然语言抽取需求倾向（`merge_text_context_state`），再直接生成推荐。需求猜错风险高，用户修正需重新开启整个会话；`evaluator` 节点只能在事后审稿防幻觉，无法纠正需求理解环节的错误。

来源：`AGENT_ARCHITECTURE.md` V1 流程、iteration-08 `README.md`。

## Decision

Agent V2 采用结构化选择卡逐步收敛需求：

```text
- 用 ask_user_choice 工具生成选择卡，单轮最多 3 个问题，每问提供预设选项并允许自定义输入。
- 用户选择直接写入 context_state，并标记来源 user_choice；字段优先级 user_choice > user_explicit_text > ai_extracted。
- 需求充分（is_sufficient）才进入线路召回，否则继续出选择卡。
- 风险上下文（has_risk_context）强制额外确认路况 / 安全偏好。
- 同一 TripPlan 会话内可连续多轮选择并修改，无需重开会话。
```

依据：`backend/app/features/trip_plans/service.py`（`_build_choice_request`）、`backend/app/features/trip_plans/context.py`（`CHOICE_WRITABLE_FIELDS`、字段来源优先级、`has_risk_context`）。

## Consequences

收益：

```text
- 需求准确性提升：用户显式选择优于 AI 文本抽取。
- 防幻觉前移：从后端 evaluator 事后审稿，前移到前端用户确认，源头减少幻觉场景。
- 用户体验：会话内即可修改，不必重开。
```

代价：

```text
- 交互复杂度上升：需要选择卡 UI 与多轮对话管理。
- 后端复杂度上升：需要管理 choice_request / choice_result 的生命周期与活跃性检查。
- Agent prompt 更结构化：workflow 中必须插入 ask_user_choice 工具调用。
```

系统级 workflow 节点序列不变，choice-based 收敛仅在 `trip_plans` 模块内增强。

## Alternatives Considered

- 继续 V1 一次性生成：放弃，需求猜错风险过高。
- 自由文本多轮对话：放弃，用户需反复开新会话，收敛不可控。
- 一次性表单收集：部分采纳，但改为渐进式选择卡（结构化 + 会话连续性兼顾）。
