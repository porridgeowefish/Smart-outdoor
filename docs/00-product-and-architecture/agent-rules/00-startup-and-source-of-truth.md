# 00 开工与事实源

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: startup order, fact-source priority, and conflict checks.

## 开工顺序

每次任务开始：

```text
1. 读取 AGENTS.md。
2. 读取 docs/INDEX.md。
3. 读取 docs/00-product-and-architecture/agent-rules/README.md。
4. 按任务触发读取对应原子规则文件。
5. 先查当前实现：代码、测试、Pydantic Schema、OpenAPI、前端生成类型。
6. 修改前说明将改哪些范围；不确定时先确认。
```

## 事实源优先级

冲突时按此顺序：

```text
1. 已实现代码、测试、Pydantic Schema、FastAPI OpenAPI 输出
2. docs/01-iterations 中当前迭代文档
3. docs/00-product-and-architecture 中长期架构和 ADR
4. docs/99-archive/backend-docs-legacy 中历史设计文档
5. design_doc 中 PRD、图和演示材料
```

PRD 表达产品愿景；MVP 迭代文档表达当前实现边界。不得仅凭 PRD 扩展 MVP 范围。

## 新旧文档冲突检查

任何设计、接口、数据库、Agent workflow、部署策略变化前，必须检查新设计是否与旧文档冲突：

```text
先查实现，再查当前迭代，再查长期架构和 ADR，最后查历史归档和 PRD。
若当前实现与文档冲突，优先相信实现，但必须指出文档需同步。
若当前迭代与长期架构冲突，按当前迭代交付边界处理，并记录是否需要 ADR。
若新设计改变架构取舍，新增 ADR，不把决策藏在聊天记录里。
若不确定是旧文档过期还是新需求变更，向人类确认。
```

## 基础事实入口

```text
docs/INDEX.md
docs/00-product-and-architecture/README.md
docs/01-iterations/README.md
```
