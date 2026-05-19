# 10 文档治理与规则追加

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
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
