# AGENTS.md：Smart_outdoor Agent 入口

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: lightweight entry point for all AI coding agents.

## 0. 使用原则

本文件只保留所有 Agent 必须常驻记住的最高优先级原则。

除“八耻八荣”外，所有项目规范都采用渐进式披露：

```text
先读本文件。
再读 docs/00-product-and-architecture/agent-rules/README.md。
然后按任务触发读取对应原子规则文件。
不要一次性把所有规则塞进上下文。
```

新增规则、事故教训、流程约束时，不直接堆进本文件；必须追加到 `docs/00-product-and-architecture/agent-rules/` 下对应原子文件，并同步更新该目录的 `README.md`。

## 1. 八耻八荣

所有 Agent 必须遵守：

```text
以瞎猜接口为耻，以认真查询为荣。
以模糊执行为耻，以寻求确认为荣。
以臆想业务为耻，以人类确认为荣。
以创造接口为耻，以复用现有为荣。
以跳过验证为耻，以主动测试为荣。
以破坏架构为耻，以遵循规范为荣。
以假装理解为耻，以诚实无知为荣。
以盲目修改为耻，以谨慎重构为荣。
```

执行含义：

```text
不确定接口、字段、命令、业务规则时，先查代码、Schema、OpenAPI、测试和迭代文档。
用户目标或业务边界仍不清楚时，先向人类确认。
现有接口、组件、工具、脚本能复用时，不新造并行方案。
改动后必须尽力验证；不能验证时说明原因和剩余风险。
```

## 2. 渐进式披露入口

按任务读取规则：

```text
docs/00-product-and-architecture/agent-rules/README.md
```

该目录负责说明：

```text
有哪些原子规则文件
什么任务触发读取哪些文件
新增规则如何归类、去重、检查冲突
长任务如何刷新上下文
```

如果 `AGENTS.md` 与规则文件冲突，以本文件的八耻八荣为最高 Agent 行为原则；其余细则以 `agent-rules/README.md` 指向的原子规则文件为准。
