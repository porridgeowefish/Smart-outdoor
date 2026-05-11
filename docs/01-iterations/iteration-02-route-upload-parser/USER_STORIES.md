# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this iteration plus implemented tests.

## US-02.1 上传线路文件

作为登录用户，我希望上传 GPX / KML / GeoJSON 文件，以便系统生成可规划的线路资产。

验收要点：

```text
支持合法文件类型
拒绝非法文件类型
可选上传 JPEG / PNG / WebP 封面图
拒绝非法封面图片类型
原始文件被保存
创建 route_asset 和 route_file
```

## US-02.2 解析轨迹指标

作为用户，我希望系统解析距离、爬升和轨迹 GeoJSON，以便后续线路展示和 Agent 推荐使用。

验收要点：

```text
解析 distance_km
解析 elevation_gain_m
生成 start_point / end_point
生成 track_geojson
解析失败返回 parse_status=failed 和 parse_error=TRACK_PARSE_FAILED
解析失败保留 route_asset / route_file，不创建 route_analysis_snapshot
```

## US-02.3 补充线路语义标签

作为用户，我希望上传时补充线路标签，以便线路可筛选和推荐。

验收要点：

```text
manual_tags 正确保存
manual_tags 必须是 JSON object
manual_tags 不替代轨迹指标或外部证据
```
