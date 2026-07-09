# Database Design

Status: superseded (API 见 Iteration 07；本轮无新表)
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM models in backend/app/features/routes/model.py。

本轮**不新增数据表**，复用 Iteration 02 的三张表。设计决策见 DELIVERY_NOTES。

## 表

```text
复用 route_assets
复用 route_files
复用 route_analysis_snapshots
```

## 复用 iter02 表

| 表 | 用途（本轮读取） | 本轮变化 |
|---|---|---|
| route_assets | 列表/详情的元数据、manual_tags、visibility、created_by_user_id | 复用 |
| route_files | 详情 primary_file（id / file_type / file_url / parse_status） | 复用 |
| route_analysis_snapshots | 列表/详情的指标与 track_geojson | 复用 |

## 派生字段（不出现在表里，由 service 计算）

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| `display_tags` | array[str] | manual_tags 列表值扁平化后前 N 个 | display_tags_from_manual_tags，limit 默认 3 | 新增（派生） |
| `location` | str | analysis_json.location.display_name 优先；其次 manual_tags.location/region/行政区/地区；缺失返回 "待识别" | _route_location | 新增（派生） |
| `track_preview.point_count` | int | len(track_geojson.coordinates)（无等距采样、无 80 点上限） | build_track_preview | 新增（派生） |

## 查询与权限规则

```text
列表可见性：
  visibility=all      → route_assets.visibility = public OR (private AND created_by_user_id = current_user.id)
  visibility=public   → 仅 visibility = public
  visibility=private  → 仅 visibility = private AND created_by_user_id = current_user.id

详情权限：
  public  → 所有登录用户可查看
  private → 仅 created_by_user_id 本人可查看

距离/爬升范围过滤在内存中进行（指标存于 snapshot 表，不直接 SQL 过滤）。
```

## 迁移与同步点

```text
本轮无 schema 变更，无须迁移。
派生字段（display_tags / location / track_preview）由 service 计算，读取点为 router。
```

## 历史来源

- ../iteration-02-route-upload-and-analysis/DATABASE_DESIGN.md（三张表来源）
- backend/app/features/routes/model.py、service.py
