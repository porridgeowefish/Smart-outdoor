# 90 简洁性、刷新与完成反馈

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: simplicity, context refresh, and completion response rules.

## 简洁性

禁止过度设计：

```text
不要为只有一个实现的场景设计抽象层。
不要提前做复杂 repository 框架。
不要迁移旧项目大块代码。
不要把 Agent 写成不可测试的面条逻辑。
不要创建无用目录和空文件。
不要创建 _v1 / _v2 这类冗余文档。
```

允许的复用：

```text
明确低耦合 utils
明确纯函数
明确 API 调用资料文档
```

## 长任务刷新点

长任务中在这些时刻必须重新读取 `AGENTS.md`、本目录 README 和相关原子规则文件：

```text
开始实现前
新增规则或教训前
改 API / Schema / 数据库前
跨后端、前端、部署边界前
测试失败并准备改策略前
准备最终回复前
上下文压缩、恢复、子代理返回后
```

## 完成反馈

每次完成任务后必须说明：

```text
改了哪些文件
完成了哪个 slice 或哪个接口
运行了哪些测试
哪些外部依赖仍是 mock
是否有未完成风险
```

每个 slice 的完成定义：

```text
测试通过
API 可调用
数据库有数据
前端能看到最小结果
契约类型已生成
mock/real 切换不改页面代码
没有无用抽象
文档已同步
```
