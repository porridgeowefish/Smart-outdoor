# Acceptance Criteria

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: this document plus automated verification after implementation lands.

## 用户闭环

```text
用户输入短需求后，前端展示选择栏，而不是只显示自然语言追问。
用户可以在同一个 TripPlan 中连续完成多轮选择。
一轮多个问题必须逐步呈现，不一次性全部铺开。
每次选择都会更新已确认条件展示。
条件足够后，系统生成最多 3 条候选线路。
推荐生成后，用户可以继续追问或修改条件。
修改关键条件后，系统可以重新收敛或重新推荐。
```

## 工具调用

```text
Agent 使用 ask_user_choice 表达待确认问题。
ask_user_choice 输入和返回均有 Pydantic schema 校验。
选择栏支持 single_choice、multi_choice 和 text/custom 输入。
基础核心字段中，departure_area / activity_goal / time_window 以 text/custom 方式收集。
偏好字段以选择题和补充输入结合的方式收集。
本轮不支持 range 控件。
工具返回用户真实选择值或自定义文本，不把 Other 当业务值。
```

## 数据与恢复

```text
choice_request 和 choice_result 均可从会话历史恢复。
trip_plans.context_state 保存已确认需求。
用户选择结果直接写入 context_state。
用户选择结果优先于 AI 抽取结果。
AI 抽取不能静默覆盖用户已确认选择。
context_state 只接受本轮白名单字段。
ability_hint 不作为默认基础核心字段；能力匹配主要来自用户能力画像。
风险场景下必须确认 terrain_tolerance 或 safety_priority 后才能推荐。
agent_runs.run_status 可以区分 waiting_user 与 succeeded。
candidate_routes 只在推荐阶段生成。
历史会话重新打开后，未完成选择仍可继续提交。
```

## 安全与表达

```text
信息不足时不生成强结论推荐。
推荐仍只能基于数据库线路、API 证据和带 URL 的外部证据。
没有证据的信息必须降级表达为未确认或建议出发前核实。
不得输出放心去、一定适合、绝对安全等禁用话术。
```

## 验证

```text
后端 API 测试通过。
关键 service / workflow 单元测试通过。
前端选择栏手动验收通过。
OpenAPI 与前端生成类型同步。
mock / real LLM 切换不改页面代码。
```
