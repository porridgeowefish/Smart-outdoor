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

当用户新增规则、教训、约束或设计原则时：

```text
1. 用 rg 搜关键词，检查是否已有同类规则或事实。
2. Agent 行为规则写入 agent-rules/ 对应原子文件。
3. 产品、架构、API、数据库、验收事实写入 docs 对应事实源。
4. 如果新增规则文件或触发条件，更新 agent-rules/README.md。
5. 最终回复说明规则落在哪、检查了哪些冲突。
```

## 文档更新时机

```text
开工前：补齐本迭代 USER_STORIES / API_CONTRACT / TEST_PLAN。
改接口：同步 Pydantic Schema、OpenAPI、迭代 API 文档。
改表结构：同步 ORM model、数据库设计、测试。
做架构取舍：新增 ADR，不把决策藏在聊天记录里。
交付后：更新 DELIVERY_NOTES 和验收状态。
```
