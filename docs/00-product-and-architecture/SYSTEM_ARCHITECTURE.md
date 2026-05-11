# 系统架构

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: migrated from PRD architecture section and component/sequence diagrams.

## 架构定位

Smart_outdoor 采用前后端分离的移动端 H5 架构，核心是有状态的户外规划 Agent，而不是单个黑盒聊天接口。

技术栈：

```text
Frontend: React 18 + TypeScript + Vite + Tailwind CSS
Backend: FastAPI + Python 3.10+
Database: MVP SQLite/PostgreSQL, future PostgreSQL
Deploy: Docker + Docker Compose
```

## 组件边界

来源图：

![组件图](../../../design_doc/组件图.png)

核心组件：

```text
User Frontend
移动端 H5，承载出去走走、我的规划、线路、个人中心。

Admin Frontend
后台管理入口，后续用于线路资产和运营管理。

FastAPI Backend
统一 API 网关和业务服务。

TripPlan Domain
规划工作区、消息、候选、快照。

Route Domain
线路资产、原始文件、轨迹解析、线路列表和详情。

User Domain
注册登录、用户资料、活动轨迹、能力画像。

Agent Orchestration
确定性 workflow 编排，控制 AgentRun 生命周期。

Evidence Tools
天气、交通、Web 搜索、LLM provider。
```

## 协作链路

来源图：

![时序图](../../../design_doc/时序图.png)

核心链路：

```text
用户发送消息
↓
FastAPI 创建或更新 TripPlan
↓
写入用户消息
↓
创建 AgentRun
↓
前端订阅 SSE
↓
Agent 读取 TripPlan / 最近消息 / 能力画像 / 线路资产
↓
Agent 更新上下文、召回路线、验证证据、生成回复
↓
SSE 推送文本、阶段、候选卡片和完成事件
```

## 设计原则

```text
有状态规划工作区，不做一次性聊天机器人
确定性 workflow 编排，不把业务边界交给自由 Agent
真实线路资产优先，不虚构路线
API 契约优先，前端类型从 OpenAPI 生成
Mock / Real 通过环境变量切换，不改页面代码
```

## MVP 与长期演进

MVP 保持简单：

```text
同步轨迹解析
SQLite 或轻量 PostgreSQL
JSON 保存上下文和分析扩展字段
mock LLM / 天气 / 交通 / 搜索可切换
不引入复杂 repository 框架
不引入 PostGIS / pgvector，除非后续 ADR 明确升级
```

长期可演进：

```text
PostgreSQL + PostGIS 空间检索
pgvector 语义召回
后台 Worker 解析轨迹
更完整的运营后台
更多外部证据源
```

