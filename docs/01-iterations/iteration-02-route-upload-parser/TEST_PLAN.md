# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: backend tests.

## API 测试

```text
上传 GPX 成功
上传 KML 成功
上传 GeoJSON 成功
拒绝非法文件类型
上传合法封面图成功
拒绝非法封面图类型
manual_tags 正确保存
manual_tags 非 JSON object 失败
解析失败返回 parse_status=failed 和 parse_error=TRACK_PARSE_FAILED
未登录不能上传
```

## Parser 测试

```text
解析距离
解析累计爬升
解析起点和终点
生成简化 track_geojson
空轨迹失败
损坏文件失败
```

## Service 测试

```text
创建 route_asset
创建 route_file
成功解析后创建 route_analysis_snapshot
失败时保存 parse_error 且不创建 route_analysis_snapshot
```
