# Acceptance Criteria

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: product acceptance and tests.

```text
个人中心可以上传一条完成轨迹。
上传成功后生成 activity_track。
上传成功后刷新 user_ability_profile。
页面可以展示活动记录列表。
页面可以展示耐力、爬坡能力、最大距离、最大爬升、可信度。
能力画像返回 generated_from_activity_track_ids、metrics_json 和 message。
没有画像时 GET /api/me/ability-profile 返回 404 ABILITY_PROFILE_NOT_FOUND。
上传 activity_track 不污染线路库。
activity_track 不会被当作 route_asset 使用。
Agent 后续可以读取 user_ability_profile 作为推荐输入。
```
