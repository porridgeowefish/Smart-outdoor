# Acceptance Criteria

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: product acceptance and tests.

```text
上传一条轨迹后数据库有 route_asset
有 route_file 原始文件记录
有 route_analysis_snapshot 指标和 track_geojson
非法文件被拒绝
合法封面图可以上传并写入 cover_image_url
非法封面图被拒绝
解析失败返回 failed 状态和 parse_error，且不创建 route_analysis_snapshot
```
