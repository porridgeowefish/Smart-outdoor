# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: this iteration plus implementation tests after this slice lands.

## US-08.1 同一会话内选择式需求收敛

作为正在规划出行的用户，我希望在同一个“出去走走”对话中通过选择栏逐步补充偏好，以便不用一次性想清楚所有条件，也不用反复开启新会话。

验收要点：

```text
用户发送自然语言后，Agent 可以返回一组待确认选择卡。
会话状态不停止，trip_plan 保持同一个 context_state。
用户每次选择后，系统把结果直接写入 context_state。
用户选择结果优先级高于 AI 从自然语言抽取出的倾向。
同一 trip_plan 可以连续出现多轮选择卡。
已确认条件和待确认条件能被前端展示。
```

## US-08.2 ask_user_choice 工具调用

作为系统维护者，我希望 Agent 通过统一的 `ask_user_choice` 工具调用向用户询问补充信息，以便选择式交互可测试、可复用，并且不会散落在自由文本回复里。

验收要点：

```text
Agent 需要用户补充信息时，产出 ask_user_choice 工具调用。
工具调用输入包含 questions 数组。
每个 question 包含 type、field、question、header、options、multi_select、allow_custom。
选项型 question 的 options 数组包含 2-4 个选项；text question 可为空数组。
一轮 ask_user_choice 最多包含 3 个问题，但前端逐步呈现，不一次性全部展开。
前端把工具调用渲染为选择栏。
用户可以选择预设选项；allow_custom=true 时可以输入自定义内容。
工具调用返回用户选择值；自定义输入返回用户文本本身。
工具调用返回值是 context_state 的高可信写入来源。
```

## US-08.3 多次选择后生成推荐

作为用户，我希望系统在我做出多个必要选择后自动生成推荐，而不是每次都只继续问问题。

验收要点：

```text
系统每次合并用户选择后运行 sufficiency_check。
当 context_state 达到推荐条件后，Agent 进入 route_retrieval。
推荐充分条件采用场景化规则：基础字段满足后，风险场景需要额外确认路况或安全偏好。
能力匹配主要读取用户能力画像；ability_hint 只作为本次强度偏好或覆盖项。
推荐仍基于数据库线路资产和既有防幻觉规则生成。
推荐响应包含 candidate_routes。
系统不得在信息不足时假装已经理解并生成强结论推荐。
```

## US-08.4 历史会话恢复选择状态

作为用户，我希望重新打开历史对话时，之前的选择问题和我的选择记录都能恢复，以便我可以继续未完成的规划。

验收要点：

```text
choice_request 作为 assistant message 的结构化 payload 落库。
choice_result 作为 user message 的结构化 payload 落库。
GET /api/trip-plans/{trip_plan_id}/messages 返回 content_type 和 payload。
未完成 choice_request 在历史会话中仍可继续提交。
已提交 choice_result 展示为可读的用户选择摘要。
```

## US-08.5 推荐后的追问与修改

作为用户，我希望看到推荐后还能继续追问、要求解释或修改条件，以便规划过程像持续会话，而不是一次性结果页。

验收要点：

```text
推荐生成后 trip_plan 仍可追加消息。
用户可以追问某条推荐为什么合适。
用户可以修改条件，例如更轻松、更近、不要冰雪路。
Agent 基于同一个 context_state、历史选择和候选结果继续回答。
修改关键条件后，系统可以重新进入需求收敛或线路召回。
```

## US-08.6 短输入、口语输入和冲突输入

作为用户，我可能只输入很短、很口语或互相冲突的需求；系统应该通过选择栏澄清，而不是猜测。

验收要点：

```text
短输入例如“周末想出去走走”会触发选择卡。
口语输入例如“想看雪但别太野”会转化为雪景、安全和路况相关选择。
冲突输入例如“轻松但要高强度爬升”会触发冲突澄清。
系统不输出绝对安全、一定适合等防幻觉禁用表达。
```
