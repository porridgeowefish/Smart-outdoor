# Agent Rules 渐进式披露索引

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: this directory owns detailed, atomic AI Agent rules referenced by `AGENTS.md`.

## 1. 设计目标

本目录用于管理 `AGENTS.md` 的各项规范，避免把所有规则一次性写进 `AGENTS.md` 导致上下文过载或长任务遗忘。

规则管理原则：

```text
AGENTS.md：只放八耻八荣和渐进式披露入口。
本目录 README：只做规则索引、触发条件和追加流程。
原子规则文件：每个文件只负责一类规范。
docs 其它文件：承载产品、架构、接口、数据库、迭代事实源。
```

## 2. 原子规则文件

| 文件 | 职责 |
|---|---|
| [00-startup-and-source-of-truth.md](./00-startup-and-source-of-truth.md) | 开工顺序、事实源优先级、新旧文档冲突检查 |
| [10-documentation-governance.md](./10-documentation-governance.md) | 文档治理、新规则/教训追加、ADR、去重 |
| [20-iteration-delivery.md](./20-iteration-delivery.md) | MVP 迭代顺序、slice 交付、完成定义 |
| [30-api-contracts.md](./30-api-contracts.md) | Pydantic、OpenAPI、前后端契约、mock/real 类型一致 |
| [40-testing-tdd.md](./40-testing-tdd.md) | TDD、最低测试要求、验证纪律 |
| [50-domain-boundaries.md](./50-domain-boundaries.md) | route_asset / activity_track、轨迹文件与渲染轨迹边界 |
| [60-agent-workflow-safety.md](./60-agent-workflow-safety.md) | Agent workflow、防幻觉、户外安全表达 |
| [70-object-storage.md](./70-object-storage.md) | 对象存储、前端直传、CORS、云端验收 |
| [80-runtime-secrets.md](./80-runtime-secrets.md) | backend/.env、部署配置、密钥安全 |
| [90-simplicity-and-refresh.md](./90-simplicity-and-refresh.md) | 简洁性、长任务刷新、完成反馈 |

## 3. 按任务触发读取

每次任务先读 `AGENTS.md` 和本 README，再按触发条件读取对应规则文件。

```text
文档治理 / 新增规则 / 事故教训：
00-startup-and-source-of-truth.md
10-documentation-governance.md
90-simplicity-and-refresh.md

某个 MVP slice / 迭代交付：
00-startup-and-source-of-truth.md
20-iteration-delivery.md
40-testing-tdd.md

API / Schema / OpenAPI / 前后端对接：
00-startup-and-source-of-truth.md
30-api-contracts.md
40-testing-tdd.md

数据库 / 领域对象 / 轨迹文件：
00-startup-and-source-of-truth.md
50-domain-boundaries.md

Agent / TripPlan / 出去走走 / 路线推荐 / 户外安全表达：
00-startup-and-source-of-truth.md
50-domain-boundaries.md
60-agent-workflow-safety.md

COS / S3 / OSS / MinIO / 图片资产 / 前端直传：
00-startup-and-source-of-truth.md
70-object-storage.md
80-runtime-secrets.md

Docker / 云端部署 / backend/.env / 密钥：
00-startup-and-source-of-truth.md
80-runtime-secrets.md

长任务 / 上下文压缩后恢复 / 最终回复前：
00-startup-and-source-of-truth.md
90-simplicity-and-refresh.md
```

## 4. 新增规则流程

当用户新增规则、教训、约束或设计原则时：

```text
1. 归类：判断是 Agent 行为规则，还是产品/架构/API/数据库/迭代事实。
2. 搜索：用 rg 搜 AGENTS.md、agent-rules/、docs/、代码、测试、Schema、OpenAPI。
3. 判冲突：按 00-startup-and-source-of-truth.md 的事实源优先级处理。
4. 落位：Agent 行为规则写入本目录对应原子文件；业务事实写入 docs 对应事实源。
5. 去重：保留单一事实源，入口只做索引或摘要。
6. 更新索引：新增文件或触发条件变化时，同步更新本 README。
7. 留痕：重大架构取舍新增 ADR；迭代范围变化同步当前 iteration 文档。
8. 复核：最终回复说明规则落在哪、检查过哪些潜在冲突。
```

禁止把聊天记录当事实源。禁止新建 `_v1` / `_v2` 这类并行文档。
