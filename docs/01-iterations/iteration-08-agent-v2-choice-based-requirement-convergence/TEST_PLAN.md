# Test Plan

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: tests required before this slice can be called done.

## Service / Unit

- choice-result 只允许写入 context_state 白名单字段；越界字段抛错。
- [US-08.1] choice-result 直接写入 context_state，并把该字段来源标为 user_choice。
- choice-result 覆盖同字段上原有的 ai_extracted 值。
- ai_extracted 不得静默覆盖已标为 user_choice 的字段。
- 用户自然语言明确修改可以覆盖 user_choice，并把来源重标为 user_explicit_text。
- choice-result 覆盖同字段旧值时，confirmed_fields 同步更新。
- field_sources 记录 user_choice / user_explicit_text / ai_extracted。
- missing_fields 只含基础核心字段或风险场景阻塞字段。
- [US-08.3] sufficiency_check 在基础核心字段满足后通过；风险场景必须额外确认 terrain_tolerance 或 safety_priority。
- ability_hint 不作为默认基础核心字段。
- 推荐后修改关键条件会创建新的 AgentRun 并重新召回；历史候选保留，conversation 默认返回最近一次 AgentRun 的候选。
- [US-08.6] 冲突输入触发 clarification choice_request，不直接召回。

## API

- POST /api/trip-plans/messages 信息不足时返回 run_status=waiting_user，含 choice_request，candidate_routes=[]。
- waiting_user 响应的 choice_request questions 每项含 type / field / question / header / options / multi_select / allow_custom。
- choice_request 一次最多 3 个问题。
- POST /choice-results 接收合法 answers 并更新 context_state。
- choice-results 提交后仍不足 → 返回下一组 choice_request；足够 → 返回 run_status=succeeded 和 candidate_routes。
- GET /api/trip-plans/{id}/messages 可恢复 choice_request 和 choice_result payload。
- confirmed_context 返回可展示摘要，不暴露完整内部 context_state。
- [US-08.5] 推荐生成后继续 POST /messages 可以追问或修改条件。
- closed TripPlan 禁止提交自然语言消息和 choice-results。

## 权限

- 用户不能提交他人 TripPlan 的 choice_request（404 CHOICE_REQUEST_NOT_FOUND）。
- 用户不能恢复或读取他人 TripPlan 的 choice payload。

## 前端

- [US-08.2] assistant message 的 choice_request 渲染为选择栏。
- 同一轮多个问题逐步呈现（单题翻页或局部卡片平移）。
- 单选只能选一个；多选可选多个；allow_custom=true 时可提交自定义输入。
- range 控件本轮不出现。
- [US-08.4] 加载历史会话时恢复未完成选择栏；只有最近一条 active choice_request 可交互。
- 选择后仍需确认时展示下一组选择栏；条件满足时展示候选线路卡片。

## 失败路径

- choice_request_id 不存在 / 不属于当前用户 / 不属于当前 TripPlan → 404 CHOICE_REQUEST_NOT_FOUND。
- choice_request 已回答 / 被新请求替代 / 非最新未回答 → 409 CHOICE_REQUEST_NOT_ACTIVE。
- field 不在白名单 → 400 INVALID_CHOICE_RESULT。
- value 不在 options 且 allow_custom=false → 400 INVALID_CHOICE_RESULT。
- multi_select=false 但 value 为数组 → 400 INVALID_CHOICE_RESULT。
- multi_select=true 但 value 非数组 → 400 INVALID_CHOICE_RESULT。
- answers 未覆盖全部 questions → 400 INVALID_CHOICE_RESULT。
- closed TripPlan → 400 TRIP_PLAN_CLOSED。

## 验证命令

```powershell
$env:DATABASE_URL='sqlite:///./test_iter8_tmp.db'; pytest tests/trip_plans/test_agent_workflow_units.py tests/trip_plans/test_trip_plan_agent_api.py
$env:DATABASE_URL='sqlite:///./test_iter8_tmp.db'; pytest
```

## 历史来源

- ../iteration-04-trip-plan-agent-mock/TEST_PLAN.md（Agent mock 基线测试）
- ../iteration-09-tag-knowledge-base-rag-choice-cards/TEST_PLAN.md（iter09 在选择卡上的增量测试）
