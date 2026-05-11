# US-01 Agent Workflow 设计

## 1. 定位

US-01 Agent Workflow 是“出去走走”对话规划模块的核心执行链路。它负责把用户自然语言、当前规划上下文、线路资产库和外部证据，转化为追问、候选线路、规划详情和可保存快照。

本设计面向 MVP 快速落地，采用结构化 workflow，而不是无边界自由 Agent。

## 2. AgentRun 输入上下文

每次用户发送消息后，系统创建一个 `agent_run`。AgentRun 输入包含 6 类信息：

```text
1. trip_plan
2. context_summary
3. context_state
4. recent_messages
5. current_user_message
6. user_ability_profile
```

示例：

```json
{
  "trip_plan": {
    "id": "tp_123",
    "status": "draft",
    "title": "成都周边一日雪山徒步"
  },
  "context_summary": "用户想从成都出发，周末找一条一日往返、能看雪山、中等强度的徒步线路。",
  "context_state": {
    "activity_goal": "看雪山",
    "departure_area": "成都",
    "time_window": {
      "raw_text": "周末",
      "start_date": "2026-05-09",
      "end_date": "2026-05-10",
      "duration_days": 1
    },
    "transport_hint": "self_drive",
    "ability_hint": {
      "level": "normal",
      "max_distance_km": null,
      "max_elevation_gain_m": null
    }
  },
  "recent_messages": [
    {"role":"user","content":"我周末想从成都出发看雪山"},
    {"role":"assistant","content":"可以，我先确认你更倾向自驾还是公共交通？"}
  ],
  "current_user_message": {
    "message_id": "msg_456",
    "content": "自驾，一天回来"
  },
  "user_ability_profile": {
    "level": "normal",
    "endurance_score": 0.62,
    "climb_score": 0.58,
    "recent_max_distance_km": 18,
    "recent_max_elevation_gain_m": 1200
  }
}
```

MVP 中 `user_ability_profile` 可以为空。为空时，Agent 使用 `context_state.ability_hint`；如果仍然缺失，则自然追问用户体能情况。

## 3. Workflow 节点

最终 Agent Workflow 采用 8 个节点：

```text
1. intent_detection
2. context_update
3. sufficiency_check
4. route_retrieval
5. evidence_search
6. plan_evaluation
7. evaluator
8. response_generation
```

### 3.1 intent_detection

职责：识别用户本轮意图。

意图类型：

```text
new_requirement
provide_info
modify_constraint
compare_candidates
ask_detail
casual
```

MVP 不单独落库意图结果。

### 3.2 context_update

职责：把用户新消息合并进当前规划记忆。

写入：

```text
trip_plans.context_summary
trip_plans.context_state
```

### 3.3 sufficiency_check

职责：判断是否达到推荐条件。

MVP 推荐触发规则：

```text
有效用户消息数 >= 2
activity_goal 已识别
 departure_area 或 current_location 已识别
time_window / transport_hint / ability_hint 至少识别出 1 个
```

信息不足时：

```text
agent_runs.run_status = waiting_user
推送 run.waiting_user
```

信息充分时：

```text
进入 route_retrieval
```

### 3.4 route_retrieval

职责：从线路资产库召回候选线路。

MVP 四层召回全部保留，但采用轻量实现：

```text
1. 硬约束过滤
2. 能力与轨迹指标匹配
3. 语义/偏好召回
4. 重排取候选池
```

#### 硬约束过滤

过滤明显不可用线路：

```text
route_assets.visibility = public
route_assets.status = active
存在可用 route_analysis_snapshot
```

#### 能力与轨迹指标匹配

使用：

```text
distance_km
elevation_gain_m
elevation_max_m
climb_ratio
steep_ratio
```

匹配：

```text
user_ability_profile
context_state.ability_hint
```

#### 语义/偏好召回

使用用户目标和线路文本/分析标签进行轻量语义评分。MVP 不引入向量库。

注意：语义召回不是关键词匹配，它只补充景观、体验、意图维度，不能替代轨迹指标。

#### 重排取候选池

综合：

```text
能力匹配
景观匹配
交通可达性
风险惩罚
多样性
```

先得到 top 10 候选池。

输出示例：

```json
{
  "retrieved_routes": [
    {
      "route_asset_id": "route_1",
      "route_analysis_snapshot_id": "analysis_1",
      "base_score": 0.81,
      "match_reasons": ["距离适中", "雪山目标匹配", "自驾可达性较好"],
      "score_parts": {
        "hard_filter_passed": true,
        "ability_score": 0.78,
        "preference_score": 0.84,
        "diversity_score": 0.7
      }
    }
  ]
}
```

### 3.5 evidence_search

职责：为候选线路补充天气、交通、外部证据和近期路况信息。

MVP 证据策略：

```text
API 可验证信息优先
网络搜索只做补充证据
不把 Tavily 当作核心可靠来源
```

证据来源分三层：

```text
1. 确定性 API 证据
天气、交通、地理位置。

2. 多源 API 保险
天气 primary = QWeather，fallback = AMap Weather 或其它天气源。
交通 primary = AMap。

3. Web 搜索补充
Tavily 只查开放网页信息，用于补充近期路况、攻略、博客、论坛、新闻。
```

网络搜索定位：

```text
Tavily 可能搜到部分抖音公开内容。
小红书检索不稳定，不能作为可靠数据源。
能搜到就引用，搜不到不编造。
```

输出示例：

```json
{
  "weather": {
    "status": "confirmed",
    "provider": "qweather",
    "summary": "2026-05-09 多云，2-12℃"
  },
  "transport": {
    "status": "confirmed",
    "provider": "amap",
    "summary": "成都自驾约 4-5 小时"
  },
  "web_evidence": {
    "status": "limited",
    "provider": "tavily",
    "summary": "未检索到足够近期的公开实走记录",
    "sources": []
  }
}
```

降级规则：

```text
天气 primary 失败：尝试 fallback。
天气 fallback 也失败：weather.status = unconfirmed。
交通失败：transport.status = unconfirmed。
Web 搜索失败或结果很少：web_evidence.status = limited / unavailable。
只要线路库召回和基础评估成功，仍然可以推荐。
证据不足必须明确说明。
```

AgentRun 状态：

```text
全部关键证据成功：succeeded
天气/交通/Web 部分失败但仍能推荐：partial
线路召回失败或候选为空：failed
```

### 3.6 plan_evaluation

职责：从候选池中选出最终 3 条推荐，并生成优势标签、推荐理由和评分拆解。

最终策略：

```text
高分 + 差异化优势 + 证据约束
```

从 top 10 候选里选择 3 条：

```text
1. 稳妥型
交通、风险、强度最平衡。

2. 目标最匹配型
比如雪山、日出、露营、挑战感最强。

3. 差异化备选型
更轻松 / 更挑战 / 更近 / 更有体验感。
```

安全门槛：

```text
明显超出用户能力的线路不推荐。
如果用户明确追求挑战，也必须标注风险。
```

最终候选写入：

```text
trip_plan_candidate_routes
```

字段：

```text
rank
advantage_tags
recommendation_reason
score_breakdown
```

优势标签最多 3 个，例如：

```text
交通便利
雪山体验
强挑战
轻量友好
一日往返
露营潜力
日出适配
风险较低
```

### 3.7 evaluator

职责：防止幻觉和越权断言。它是最终输出前的审稿人节点。

本质：

```text
把 AI 从自由生成器降级为有证据约束的解释器。
```

采用：

```text
Grounded Generation
Evidence Required Schema
Evaluator
降级表达
```

检查内容：

```text
无证据断言
近期路况幻觉
天气/交通来源缺失
能力不匹配风险
绝对安全话术
推荐理由是否有依据
```

MVP 实现方式：

```text
规则检查先跑一遍
LLM Evaluator 再审一遍
如果 failed，则让 response_generation 降级表达
```

检查规则：

```text
1. 近期路况/实走记录必须有 web evidence URL，否则只能说未确认。
2. 天气必须来自天气 API，否则只能说天气未确认。
3. 交通耗时必须来自 AMap 或明确估算来源，否则标记未确认。
4. 如果线路距离/爬升明显超过用户能力，必须有风险提醒。
5. 禁止“放心去”“没问题”“一定适合”这类绝对话术。
6. 推荐理由必须来自 route_analysis + 用户需求 + evidence，不能凭空写。
```

Evaluator 输出示例：

```json
{
  "passed": false,
  "issues": [
    {
      "field": "risk_notes",
      "type": "unsupported_claim",
      "message": "声称近期路况良好，但没有 Web/API 证据。"
    }
  ],
  "required_edits": [
    {
      "field": "transport_plan.summary",
      "action": "downgrade_to_unconfirmed"
    }
  ]
}
```

核心规则：

```text
没有证据的内容不能作为确定结论。
没有证据的信息只能表达为未确认、证据不足、建议出发前核实。
```

### 3.8 response_generation

职责：把 Agent 内部结果转成用户能理解、愿意继续对话的输出。

它不重新推荐，不重新做判断，只负责表达和事件推送。

信息不足时推送：

```text
message.delta
message.completed
run.waiting_user
run.completed
```

表达策略：

```text
先接住用户需求
说明已经理解了什么
自然追问一个最关键问题
给最多 3 个选项
允许用户自由输入
```

信息充分时推送：

```text
run.phase_changed
message.delta
message.completed
candidate_routes.updated
run.completed
```

表达策略：

```text
说明筛选逻辑
给出 3 条候选
明确未确认项
邀请用户点开详情或继续追问
```

禁止话术：

```text
一定适合
放心去
路况很好
最近很多人走过
绝对安全
```

落库：

```text
trip_plan_messages(role=assistant)
```

## 4. 数据写入规则

| 节点 | 写入位置 | 说明 |
|---|---|---|
| intent_detection | 不单独落库 | MVP 暂不保存意图历史。 |
| context_update | trip_plans | 写 `context_summary` 和 `context_state`。 |
| sufficiency_check | agent_runs | 不足时 `run_status = waiting_user`。 |
| route_retrieval | 不保存中间池 | 最终候选由 plan_evaluation 写入。 |
| evidence_search | 不单独建表 | 证据跟随候选详情或 snapshot 保存为 JSON。 |
| plan_evaluation | trip_plan_candidate_routes | 写最终 3 条候选。 |
| evaluator | 不单独落库 | MVP 可写入日志，正式版可持久化。 |
| response_generation | trip_plan_messages | 写 assistant 最终消息。 |

## 5. SSE 输出规则

| 场景 | SSE 事件 |
|---|---|
| 阶段变化 | run.phase_changed |
| 流式文本 | message.delta |
| 文本完成 | message.completed |
| 需要追问 | run.waiting_user |
| 候选卡片生成 | candidate_routes.updated |
| 正常完成 | run.completed |
| 失败 | run.failed |

## 6. Workflow 总结

```text
intent_detection
→ context_update
→ sufficiency_check
→ route_retrieval
→ evidence_search
→ plan_evaluation
→ evaluator
→ response_generation
```

分支：

```text
信息不足：
intent_detection
→ context_update
→ sufficiency_check
→ response_generation
→ run.waiting_user

信息充分：
intent_detection
→ context_update
→ sufficiency_check
→ route_retrieval
→ evidence_search
→ plan_evaluation
→ evaluator
→ response_generation
→ candidate_routes.updated
```
