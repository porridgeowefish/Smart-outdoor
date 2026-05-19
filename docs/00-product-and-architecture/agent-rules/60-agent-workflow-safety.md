# 60 Agent Workflow 与防幻觉

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: Agent workflow and anti-hallucination rules.

## 读取入口

```text
docs/00-product-and-architecture/AGENT_ARCHITECTURE.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/
docs/00-product-and-architecture/DOMAIN_MODEL.md
```

## 适用场景

```text
出去走走
TripPlan
AgentRun
路线推荐
证据搜索
户外安全表达
```

## 防幻觉规则

```text
Agent 只能基于数据库已有信息、API 明确返回的信息、Web 搜索明确返回且带 URL 的信息输出。
无证据内容必须降级表达为：未确认、证据不足、建议出发前核实。
禁止输出：放心去、一定适合、路况很好、最近很多人走过、绝对安全。
除非证据明确支持，且仍应保守表达。
不得把 Agent 写成不可测试的单体函数。
```

## 固定 Workflow

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
