# Smart_outdoor 文档入口

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this file is the entry point; linked documents own their domain details.

本文件是人和 AI coding agent 的统一文档入口。开始开发前先读这里，再按任务进入对应模块。

## 文档分层

项目文档分成三类：

```text
00-product-and-architecture
需求分析、产品建模、领域边界、系统架构、关键架构决策。

01-iterations
按敏捷迭代组织的交付文档。每一轮迭代必须包含用户故事、API、数据库、测试和验收。

99-archive
历史文档归档。只作为追溯材料，不作为当前实现契约。
```

## 当前事实源优先级

当文档之间出现冲突时，按以下顺序判断：

```text
1. 已实现代码、测试、Pydantic Schema、FastAPI OpenAPI 输出
2. docs/01-iterations 中当前迭代文档
3. docs/00-product-and-architecture 中长期架构和 ADR
4. docs/99-archive/backend-docs-legacy 中历史设计文档
5. design_doc 中 PRD、图和演示材料
```

PRD 表达产品愿景；MVP 迭代文档表达当前实现边界。不得仅凭 PRD 扩展 MVP 范围。

## 必读入口

- 文档治理规范：[DOCUMENTATION_STANDARD.md](./00-product-and-architecture/DOCUMENTATION_STANDARD.md)
- 产品与架构入口：[00-product-and-architecture/README.md](./00-product-and-architecture/README.md)
- 核心资产索引：[ASSET_INDEX.md](./00-product-and-architecture/ASSET_INDEX.md)
- PRD 摘要：[PRD.md](./00-product-and-architecture/PRD.md)
- 领域模型：[DOMAIN_MODEL.md](./00-product-and-architecture/DOMAIN_MODEL.md)
- Agent 架构：[AGENT_ARCHITECTURE.md](./00-product-and-architecture/AGENT_ARCHITECTURE.md)
- MVP 路线图：[MVP_ROADMAP.md](./00-product-and-architecture/MVP_ROADMAP.md)
- 未来规划草案：[FUTURE_PLANNING.md](./00-product-and-architecture/FUTURE_PLANNING.md)
- 敏捷迭代入口：[01-iterations/README.md](./01-iterations/README.md)

## 当前迭代顺序

```text
Iteration 01 Auth + User
Iteration 02 Route Upload + Parser
Iteration 03 Route List + Detail
Iteration 04 TripPlan + Agent Workflow
Iteration 05 Snapshot / 我的规划
Iteration 06 Ability Profile
Iteration 07 Object Storage + Image Assets
```

## 历史文档归档映射

后端旧设计文档已迁移到 `docs/99-archive/backend-docs-legacy`。归档文档只用于追溯历史设计来源；如果与当前迭代契约或代码冲突，以当前迭代契约和代码为准。

| 历史文档 | 新位置 / 说明 |
|---|---|
| `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md` | MVP 切片顺序历史来源 |
| `docs/99-archive/backend-docs-legacy/US-01_API_CONTRACT.md` | TripPlan / Snapshot 早期 API 设计 |
| `docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md` | 数据库总模型早期设计 |
| `docs/99-archive/backend-docs-legacy/US-01_AGENT_WORKFLOW.md` | Agent 工作流早期设计 |
| `docs/99-archive/backend-docs-legacy/US-02_PROFILE_AND_ABILITY_DESIGN.md` | 用户与能力画像早期设计 |
| `docs/99-archive/backend-docs-legacy/US-03_ROUTE_MODULE_DESIGN.md` | 线路模块早期设计 |
| `docs/99-archive/backend-docs-legacy/API_USAGE_REFERENCE.md` | 外部 API 调用参考 |
| `design_doc/智行户外PRD.docx` | 产品愿景、用户洞察、方案建模 |
| `design_doc/*.png`, `design_doc/*.drawio` | 架构图、流程图、ER 图 |

## 文档更新时机

```text
开工前：补齐本迭代 USER_STORIES / API_CONTRACT / TEST_PLAN。
改接口：同步 Pydantic Schema、OpenAPI、迭代 API 文档。
改表结构：同步 ORM model、数据库设计、测试。
做架构取舍：新增 ADR，不把决策藏在聊天记录里。
交付后：更新 DELIVERY_NOTES 和验收状态。
```
