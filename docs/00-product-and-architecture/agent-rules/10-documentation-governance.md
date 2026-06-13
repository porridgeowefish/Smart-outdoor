# 10 文档治理与规则追加

Status: active
Owner: project maintainer
Last reviewed: 2026-05-21
Source of truth: documentation governance and Agent rule maintenance.

## 读取入口

```text
docs/INDEX.md
docs/00-product-and-architecture/DOCUMENTATION_STANDARD.md
AGENTS.md
docs/00-product-and-architecture/agent-rules/README.md
```

## 文档治理

```text
入口文档只做索引和摘要，不复制长事实源。
禁止维护多份重复事实源。
禁止创建 _v1 / _v2 这类并行文档。
不得把聊天记录当事实源。
重大架构取舍新增 ADR。
```

## 对齐产物与事实源

需求、架构、接口、数据库和验收口径仍以 Markdown 文档作为共识事实源。HTML 只作为对齐、可视化判断和反馈采集工具。

```text
Markdown：用于积累共识、形成迭代契约、承载最终事实。
HTML：用于让人类翻页阅读、交互选择、做决策判断、导出回答。
导出的回答 Markdown：用于承接人类反馈，不能自动等同于最终事实。
正式迭代文档：必须由 Agent 在读取导出回答后，按规则整理、去重、检查冲突并写入。
```

当用户说“对齐完毕”时：

```text
1. 读取用户从 HTML 导出的回答 Markdown。
2. 把回答与当前迭代文档、代码、Schema、测试和既有规则对照。
3. 只把确认后的结论写入正式 Markdown 文档。
4. 不把 HTML 页面本身当作事实源。
5. 不把聊天记录当作事实源。
```

## 新规则/教训追加

当用户新增规则、教训、约束或设计原则时，流程见 [agent-rules/README.md 第 4 节](./README.md)。要点：先归类、再搜索判冲突、落位到原子文件或事实源、保留单一事实源、更新本目录 README、重大架构取舍留 ADR。

## 文档更新时机

开工 / 接口 / 表结构 / 交付的总表见 [docs/INDEX.md](../../INDEX.md)。架构变更需额外同步长期架构文档：

### 架构变更落点表

| 变更类型 | 新增 ADR | 同步更新 |
|---|---|---|
| 技术栈 / 基础设施取舍 | ✓ | SYSTEM_ARCHITECTURE.md（技术栈、组件边界、协作链路）|
| 数据模型边界取舍 | ✓ | DATA_MODEL.md（表分组、字段、对象存储字段）|
| Agent workflow 关键策略 | ✓ | AGENT_ARCHITECTURE.md（节点职责、状态机）|
| Mock / Real 切换策略 | ✓ | SYSTEM_ARCHITECTURE.md（设计原则：mock 切换）|
| 安全 / 隐私 / 证据约束 | ✓ | 相关 00 文档 + agent-rules 原子文件（60 / 70 / 80）|

规则：更新文档内容时同步更新该文档的 Last reviewed 日期。
