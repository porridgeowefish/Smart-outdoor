# 产品与架构文档

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: `docs/INDEX.md` routes readers here; each linked document owns its topic.

本目录保存长期稳定的建模文档，用来回答：

```text
为什么做
做什么
边界在哪里
为什么这样设计
哪些架构决策已经确定
```

这里不记录每日进度，不写某个 slice 的临时交付细节。

## 核心文档

| 文档 | 用途 | 来源 |
|---|---|
| [ASSET_INDEX.md](./ASSET_INDEX.md) | PRD、图片、drawio、旧设计文档资产索引 | `design_doc/`, `docs/99-archive/backend-docs-legacy/` |
| [PRD.md](./PRD.md) | 产品愿景、目标用户、核心痛点、核心场景 | `design_doc/智行户外PRD.docx` |
| [USER_RESEARCH.md](./USER_RESEARCH.md) | 用户洞察和问题定义 | PRD 模块一 |
| [PRODUCT_FLOW.md](./PRODUCT_FLOW.md) | 产品主流程、线路流程、轨迹流程、个人中心流程 | PRD、流程图 |
| [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) | 核心领域对象和边界 | PRD、US-01/02/03 |
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) | 系统上下文、组件边界、协作链路 | PRD、组件图、时序图 |
| [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) | Agent workflow、证据约束、防幻觉策略 | PRD、Agent 图、US-01 Agent Workflow |
| [DATA_MODEL.md](./DATA_MODEL.md) | 全局数据模型和核心关系 | ER 图、US-01 数据库设计 |
| [API_CONTRACT_STRATEGY.md](./API_CONTRACT_STRATEGY.md) | 契约驱动、OpenAPI、前后端类型生成原则 | API 契约文档 |
| [MVP_ROADMAP.md](./MVP_ROADMAP.md) | MVP 迭代顺序和完成定义 | MVP 实施切片计划 |
| [FUTURE_PLANNING.md](./FUTURE_PLANNING.md) | 后续候选迭代想法、业务价值和大致实现草案 | 跨对话规划讨论 |
| [agent-rules/](./agent-rules/README.md) | AI Agent 原子规则与渐进式披露索引 | `AGENTS.md` |
| [DOCUMENTATION_STANDARD.md](./DOCUMENTATION_STANDARD.md) | 文档管理规范 | 本次文档治理结论 |
| [ADR/](./ADR/) | 架构决策记录 | 架构决策 |

## 当前历史来源

- `design_doc/智行户外PRD.docx`
- `design_doc/*.png`
- `design_doc/*.drawio`
- `docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md`
- `docs/99-archive/backend-docs-legacy/US-01_AGENT_WORKFLOW.md`
- `docs/99-archive/backend-docs-legacy/US-02_PROFILE_AND_ABILITY_DESIGN.md`
- `docs/99-archive/backend-docs-legacy/US-03_ROUTE_MODULE_DESIGN.md`

## 与迭代文档的关系

产品与架构文档定义长期方向；迭代文档定义当前交付边界。

如果二者冲突：

```text
当前迭代以 docs/01-iterations 对应目录为准。
长期架构变化必须新增或更新 ADR。
```
