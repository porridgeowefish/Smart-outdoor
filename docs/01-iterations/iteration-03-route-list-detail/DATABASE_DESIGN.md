# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: ORM model and migrations when introduced.

本轮复用 Iteration 02 中的三类对象：

```text
route_assets
route_files
route_analysis_snapshots
```

## 查询规则

列表默认返回：

```text
route_assets.visibility = public
+
route_assets.visibility = private AND created_by_user_id = current_user.id
```

`visibility=all` 与默认规则一致，不表示返回全库 private 线路。

其他查询规则：

```text
visibility=public 只返回 public
visibility=private 只返回 current_user 自己创建的 private
```

详情权限：

```text
public：所有登录用户可查看
private：只有 created_by_user_id 本人可查看
```

## 派生字段

```text
display_tags
当前来源于 manual_tags 的列表值扁平化结果，最多取前 3 个
用于卡片展示 2-3 个重点标签

location
优先来自 analysis_json.location.display_name，其次来自 manual_tags 中的 location / region / 行政区 / 地区，缺失时返回“待识别”

track_preview
来源于 route_analysis_snapshots.track_geojson，用于列表卡片轻量轨迹预览
当前实现对 coordinates 做等距索引采样，最多 80 个点
```
