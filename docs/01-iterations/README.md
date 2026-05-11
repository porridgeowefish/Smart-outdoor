# 敏捷迭代文档

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: iteration subdirectories define delivery scope.

本目录按用户闭环组织交付文档。每一轮迭代必须能独立验收。

## 迭代顺序

| 迭代 | 用户闭环 | 目录 |
|---|---|---|
| 01 | Auth + User | [iteration-01-auth-user](./iteration-01-auth-user/README.md) |
| 02 | Route Upload + Parser | [iteration-02-route-upload-parser](./iteration-02-route-upload-parser/README.md) |
| 03 | Route List + Detail | [iteration-03-route-list-detail](./iteration-03-route-list-detail/README.md) |
| 04 | TripPlan + Agent Mock | [iteration-04-trip-plan-agent-mock](./iteration-04-trip-plan-agent-mock/README.md) |
| 05 | Snapshot / 我的规划 | [iteration-05-snapshot-my-plans](./iteration-05-snapshot-my-plans/README.md) |
| 06 | Ability Profile | [iteration-06-ability-profile](./iteration-06-ability-profile/README.md) |

## 每轮必备文档

```text
README.md
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

当前先建立 `README.md` 骨架。后续开发某一轮前，必须补齐该轮详细文档。

## 完成定义

```text
测试通过
API 可调用
数据库有数据
前端能看到最小结果
契约类型已生成
mock/real 切换不改页面代码
没有无用抽象
```

