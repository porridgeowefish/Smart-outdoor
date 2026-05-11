# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## GET /api/routes

用途：线路列表、搜索和标签筛选。

Query:

```text
keyword
visibility = public / private / all
min_distance_km
max_distance_km
min_elevation_gain_m
max_elevation_gain_m
tags
tag_match_mode = any / all
page
page_size
```

Response:

```json
{
  "items": [
    {
      "route_id": "route_1",
      "name": "四姑娘山大峰",
      "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
      "location": "四川省 · 阿坝藏族羌族自治州",
      "visibility": "public",
      "distance_km": 15.2,
      "elevation_gain_m": 1320,
      "manual_tags": {},
      "display_tags": ["雪山", "自驾友好"],
      "track_preview": {
        "format": "geojson",
        "coordinate_system": "wgs84",
        "point_count": 120,
        "geojson": {
          "type": "LineString",
          "coordinates": [[102.9, 31.0], [102.91, 31.01]]
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

字段说明：

```text
cover_image_url
线路封面图 URL，用于卡片主图。

track_preview
线路轨迹轻量预览，用于列表卡片中的小地图或路线轮廓，不是封面图。
当前实现从 route_analysis_snapshots.track_geojson.coordinates 等距采样，最多 80 个点。
它不是 Douglas-Peucker 等高保真几何压缩算法。

manual_tags
用户上传线路时保存的原始标签字典。

display_tags
从 manual_tags 的列表值扁平化后取前 3 个，用于卡片快速展示。
当前实现不从 analysis_json 派生 display_tags。
```

权限规则：

```text
visibility=all 表示 public + 当前用户自己的 private
visibility=public 只返回 public
visibility=private 只返回当前用户自己的 private
其他用户 private 不会返回
```

## GET /api/routes/tag-taxonomy

用途：获取前端线路标签选择器使用的标签分类。

Response:

```json
{
  "categories": [
    {
      "key": "scenery",
      "label": "风光与场景",
      "tags": ["森林", "溪流", "雪山"]
    }
  ]
}
```

## GET /api/routes/{route_id}

用途：线路本体详情。

Response:

```json
{
  "route_id": "route_1",
  "name": "四姑娘山大峰",
  "description": "经典雪山体验路线",
  "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
  "location": "四川省 · 阿坝藏族羌族自治州",
  "visibility": "public",
  "source_type": "user_upload",
  "source_name": null,
  "manual_tags": {
    "scenery": ["雪山"],
    "transport_facility": ["自驾友好"]
  },
  "analysis": {
    "route_analysis_snapshot_id": "analysis_1",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "elevation_loss_m": 1320,
    "elevation_min_m": 3200,
    "elevation_max_m": 5025,
    "climb_ratio": 86.8,
    "steep_ratio": null,
    "start_point": {"lon": 102.9, "lat": 31.0},
    "end_point": {"lon": 102.91, "lat": 31.01},
    "bounds": {
      "min_lon": 102.9,
      "min_lat": 31.0,
      "max_lon": 102.91,
      "max_lat": 31.01
    },
    "center_point": {"lon": 102.905, "lat": 31.005},
    "analysis_json": {}
  },
  "track": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "simplified": true,
    "point_count": 842,
    "geojson": {
      "type": "LineString",
      "coordinates": [[102.9, 31.0], [102.91, 31.01]]
    }
  },
  "primary_file": {
    "file_id": "file_1",
    "file_type": "gpx",
    "file_url": "/static/routes/route_1/file_1.gpx",
    "parse_status": "parsed"
  },
  "actions": {
    "can_send_to_trip_plan": true,
    "can_download_file": false,
    "can_edit": true
  }
}
```

字段说明：

```text
visibility
线路资产可见性，public / private。用于详情展示，不是权限判断本身。

actions
当前详情响应里的 UI 能力标志。
can_send_to_trip_plan 当前恒为 true，但本迭代没有实现 send-to-trip-plan API。
can_download_file 当前恒为 false，本迭代没有实现下载 API。
can_edit 表示创建者或 admin 的编辑入口可见性，本迭代没有实现编辑 API。
```

设计边界：

```text
不返回本次规划建议
不查询天气
不查询交通
不生成 snapshot
```
