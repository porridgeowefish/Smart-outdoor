# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this iteration plus implemented tests.

## US-03.1 查看线路列表

作为登录用户，我希望查看 public 线路和我自己的 private 线路，以便找到可规划路线。

验收要点：

```text
默认返回 public + 当前用户 private
不返回其他用户 private
支持分页
支持关键词和标签筛选
列表返回 location
列表返回 track_preview，用于小地图或路线轮廓预览
可以获取标签 taxonomy
```

## US-03.2 查看线路详情

作为用户，我希望查看线路详情和轨迹地图，以便判断线路本身是否值得规划。

验收要点：

```text
详情返回 route_asset 基础信息
详情返回 analysis 指标
详情返回 track.geojson
详情返回 primary_file
详情返回 visibility
详情返回 actions 标志，但本轮不交付 send-to-trip-plan / 下载 / 编辑接口
不调用 Agent、天气或交通
```
