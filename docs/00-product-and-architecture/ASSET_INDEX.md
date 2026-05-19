# 核心资产索引

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this file indexes migrated product and architecture assets; original files remain in `design_doc/` and `docs/99-archive/backend-docs-legacy/`.

本文件把 PRD、PRD 图片、流程图、架构图和旧迭代规划文档中的核心资产统一登记到产品与架构模块。

## 原始资产

| 资产                                                 | 用途                           |
| -------------------------------------------------- | ---------------------------- |
| `design_doc/智行户外PRD.docx`                          | 产品愿景、用户洞察、痛点、场景、AI 原生能力、商业分析 |
| `design_doc/Agent.png`                             | Agent 架构示意                   |
| `design_doc/Agent状态机图.png`                         | Agent / TripPlan 状态机         |
| `design_doc/Agent顺序流程图.png`                        | Agent 顺序工作流                  |
| `design_doc/组件图.png`                               | 系统组件边界                       |
| `design_doc/组件图graph.png`                          | 组件关系图                        |
| `design_doc/时序图.png`                               | 用户请求到 Agent 输出的协作链路          |
| `design_doc/数据库ER图.png`                            | 全局 ER 图                      |
| `design_doc/轨迹资产相关流程图.png`                         | 轨迹资产上传、解析和使用流程               |
| `design_doc/线路展示流程图.png`                           | 线路列表、详情、转发规划流程               |
| `design_doc/个人信息流程图.png`                           | 用户资料、活动轨迹、能力画像流程             |
| `design_doc/一个规划的状态图.png`                          | 单个规划状态流转                     |
| `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`        | MVP 切片顺序与完成定义                |
| `docs/99-archive/backend-docs-legacy/US-01_AGENT_WORKFLOW.md`             | Agent Workflow 详细设计          |
| `docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md`            | 数据库总模型                       |
| `docs/99-archive/backend-docs-legacy/US-01_API_CONTRACT.md`               | TripPlan / Snapshot API 契约   |
| `docs/99-archive/backend-docs-legacy/US-02_PROFILE_AND_ABILITY_DESIGN.md` | 用户与能力画像设计                    |
| `docs/99-archive/backend-docs-legacy/US-03_ROUTE_MODULE_DESIGN.md`        | 线路模块设计                       |

## 已迁移 Markdown

| 新文档 | 来源 |
|---|---|
| [PRD.md](./PRD.md) | `design_doc/智行户外PRD.docx` |
| [USER_RESEARCH.md](./USER_RESEARCH.md) | PRD 用户洞察与痛点 |
| [PRODUCT_FLOW.md](./PRODUCT_FLOW.md) | PRD UI 与交互流程、线路/个人信息流程图 |
| [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) | PRD、US-01/02/03 领域边界 |
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) | PRD 产品架构、组件图、时序图 |
| [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) | PRD AI 技术方案、US-01 Agent Workflow |
| [DATA_MODEL.md](./DATA_MODEL.md) | US-01 数据库设计、ER 图 |
| [API_CONTRACT_STRATEGY.md](./API_CONTRACT_STRATEGY.md) | API 契约文档、OpenAPI 规则 |
| [MVP_ROADMAP.md](./MVP_ROADMAP.md) | MVP 实施切片计划 |

## 图片引用

Markdown 文档引用原始图片，不复制二进制文件。后续如果需要发布独立文档站，再把图片迁入 `docs/00-product-and-architecture/assets/`。

## 文件资产存储迭代

头像、路线封面和路线原始轨迹文件的 URL 化与对象存储改造放在：

```text
docs/01-iterations/iteration-07-object-storage-image-assets/
```

该迭代文档承接 [FUTURE_PLANNING.md](./FUTURE_PLANNING.md) 中的 `Object Storage + Image Assets` 规划。长期领域边界仍以 [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) 和 [DATA_MODEL.md](./DATA_MODEL.md) 为准。
