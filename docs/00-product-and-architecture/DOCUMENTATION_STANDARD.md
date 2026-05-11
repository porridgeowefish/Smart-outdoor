# 文档管理规范

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this document defines documentation rules for Smart_outdoor.

## 1. 核心原则

Smart_outdoor 使用：

```text
docs-as-code + 文档驱动开发 + 敏捷切片交付
```

文档和代码在同一仓库维护，接口、数据库、Agent workflow、测试策略变化时，文档必须在同一轮任务中同步更新。

## 2. 单一事实源

禁止为同一件事维护多份互相复制的长文档。

允许：

```text
入口文档做索引
总览文档做摘要
详细文档拥有事实源
```

禁止：

```text
在 AGENTS.md、CLAUDE.md、README、迭代文档中重复粘贴同一份长 API 契约
旧文档改名为 _v1 / _v2 后继续并行维护
用聊天记录替代 ADR
```

## 3. 两类文档

### 3.1 需求分析与架构设计

位置：

```text
docs/00-product-and-architecture/
```

内容：

```text
用户洞察
产品场景
领域模型
系统架构
Agent 架构
数据模型
API 契约策略
ADR
```

不包含：

```text
每日进度
临时讨论
某个 slice 的详细测试清单
```

### 3.2 敏捷迭代交付

位置：

```text
docs/01-iterations/iteration-XX-name/
```

每一轮迭代必须包含：

```text
README.md
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

迭代文档只描述本轮交付，不重复长期架构全文。

## 4. API 契约规则

最终事实源：

```text
FastAPI route
Pydantic V2 Request / Response model
/openapi.json
前端 OpenAPI 生成类型
```

Markdown API 文档只解释：

```text
接口用途
业务规则
错误码
关键样例
验收重点
```

禁止前端手写后端 Response 类型。

## 5. 数据库文档规则

数据库设计必须说明：

```text
本轮新增/修改表
字段含义
关键约束
权限与归属规则
与已有领域对象的关系
```

全局数据模型放在架构模块；本轮落地细节放在迭代模块。

## 6. ADR 规则

当出现以下情况时必须新增 ADR：

```text
技术栈或基础设施取舍
数据模型边界取舍
Agent workflow 关键策略
Mock / Real 切换策略
安全、隐私、证据约束策略
```

ADR 模板：

```text
# ADR-NNNN Title

Status: proposed | accepted | superseded
Date: YYYY-MM-DD

## Context
## Decision
## Consequences
## Alternatives Considered
```

已接受 ADR 不回改历史结论；新决策新增 ADR 并标记 supersedes。

## 7. AI Agent 协作规则

AI coding agent 开工前必须：

```text
1. 读取 docs/INDEX.md
2. 判断任务属于产品架构还是某轮迭代
3. 读取对应目录的 README 和相关事实源
4. 若文档缺失，先补文档草案，再实现
```

AI 不得：

```text
基于 PRD 愿景直接扩大 MVP 范围
忽略当前迭代验收标准
绕过 OpenAPI 类型生成约束
把无证据户外安全结论写成确定事实
```

## 8. 文档状态字段

长期文档建议包含：

```text
Status
Owner
Last reviewed
Source of truth
```

状态建议：

```text
draft
active
deprecated
superseded
```

## 9. 完成定义

一个迭代完成时，文档必须满足：

```text
用户故事清楚
API 契约已实现或明确标记 pending
数据库设计与代码一致
测试计划有对应测试或说明
验收标准可以人工验证
DELIVERY_NOTES 记录实际交付和遗留风险
```

