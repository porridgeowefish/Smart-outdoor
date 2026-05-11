# ADR-0001 Documentation Structure

Status: accepted
Date: 2026-05-08

## Context

项目已有两类文档：

```text
design_doc 中的 PRD、流程图、架构图和演示材料
docs/99-archive/backend-docs-legacy 中的 API、数据库、Agent workflow、MVP 切片设计
```

这些文档内容有价值，但当前混在不同目录和同一层级中。AI coding agent 接手任务时，难以判断哪些是长期产品愿景，哪些是当前 MVP 迭代事实源。

## Decision

建立新的顶层 `docs/` 目录，按两类文档组织：

```text
docs/00-product-and-architecture/
docs/01-iterations/
```

`docs/INDEX.md` 作为人和 AI agent 的统一入口。

历史文档暂不移动，先通过索引和迁移映射引用，避免一次性大搬迁破坏引用。

## Consequences

收益：

```text
文档入口清晰
长期架构和迭代交付分离
AI agent 更容易定位事实源
后续可以逐步迁移旧文档
```

代价：

```text
短期内存在新旧目录并存
需要在后续迭代中逐步把旧文档拆分到新结构
```

## Alternatives Considered

直接移动所有旧文档到新目录。

放弃原因：当前仓库已有代码和文档引用旧路径，一次性迁移风险较高。

