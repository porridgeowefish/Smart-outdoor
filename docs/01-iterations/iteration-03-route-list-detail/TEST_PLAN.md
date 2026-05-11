# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: backend tests.

## API 测试

```text
默认返回 public + 当前用户 private
不返回其他用户 private
visibility=public 只返回 public
visibility=private 只返回当前用户 private
tags 筛选 any
tags 筛选 all
GET /api/routes/tag-taxonomy 返回标签分类
列表返回 location
列表返回 track_preview，且 preview coordinates 不超过 80 个点
详情返回 analysis
详情返回 track.geojson
详情返回 primary_file
详情返回 actions
private 详情权限正确
```

## Service 测试

```text
display_tags 生成稳定
display_tags 从 manual_tags 扁平化后最多取 3 个
location 从 analysis_json 或 manual_tags 派生
track_preview 使用等距索引采样
无 analysis 的线路不破坏列表响应
分页 total 正确
```
