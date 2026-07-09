# Delivery Notes

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation notes.

## 交付内容

- 历史迭代，未记录逐次交付日志；以下能力据现存代码与文档确认已落地：
- `activity_tracks` / `user_ability_profiles` 两张表（ORM 见 backend/app/features/users/model.py）。
- POST /api/me/activity-tracks/upload：上传完成轨迹、解析、反查位置、刷新画像。
- GET /api/me/activity-tracks：完成活动列表。
- GET /api/me/ability-profile：当前用户画像。
- 能力算法 `ability_v1`：耐力 / 爬坡归一化、level 阈值、metrics_json 补充指标（backend/app/features/users/activity_service.py）。

## 测试运行

```powershell
pytest backend/tests/users/test_activity_ability_api.py
```

历史迭代，未记录当次运行结果；测试用例现存，覆盖 upload 成功 / 404 profile / 列表与画像累积 / 非法文件类型等路径。

## 遗留风险

- `type` 当前固定为 `hike`，扩展多运动类型会破坏列表语义。
- 反查位置失败时 `analysis_json.location` 缺省、列表 location 回退 `"待识别"`；定位精度依赖高德反查可用性。
- 上传成功固定返回 `parse_status=parsed`，无 `failed` 终态；当前无重试或异步解析通道。
- 轨迹文件落本地静态目录（config `activity_storage_dir`），未迁到对象存储。
- confidence 规则偏粗（见下“对齐与决策”），随业务沉淀可能需要重新标定阈值。

## 对齐与决策

### activity_track vs route_asset 边界（边界论证）

```text
activity_track 是用户完成记录，route_asset 是线路资产。
activity_track 默认不进入线路库。
route_asset 不会自动成为 activity_track。
上传 activity_track 成功会更新 user_ability_profile。
上传 activity_track 失败不会保存 failed 状态记录。
```

### 上传与解析行为

```text
上传成功固定返回 parse_status=parsed。
解析失败不保存 activity_track，也不生成 failed 状态记录；直接返回 400 TRACK_PARSE_FAILED。
activity_track 是用户已完成活动，不会创建 route_asset，也不进入线路库。
列表按 activity_date desc、created_at desc 排序。
month 当前返回 activity_date.month 的字符串，例如 "5"。
location 取 analysis_json.location.display_name；反查无结果返回 "待识别"。
type 当前固定 "hike"。
pace_or_speed 据 moving_time_seconds 与 distance_km 计算；缺时间或距离无效返回 "--"。
GET /api/me/ability-profile 在用户尚未上传成功任何 activity_track 时返回 404 ABILITY_PROFILE_NOT_FOUND，不返回 unknown profile。
```

### confidence 规则

confidence 不只按活动数量，还参考活动分析质量：

```text
activity_count = 0                          -> unknown
activity_count <= 2 且 good quality < 2 条  -> low
activity_count <= 2 且 good quality >= 2 条 -> medium
activity_count 3-4                          -> medium
activity_count >= 5                         -> high
```

## 暴露的权衡

- 为不污染线路库，activity_track 与 route_asset 严格分离；后续若需“把完成轨迹提升为线路”需另开迭代。
- 为简化首轮，能力算法固定为 `ability_v1`，归一化区间硬编码；后续调整阈值需考虑历史画像一致性。
- 反查位置依赖外部高德服务；不可用时以 `"待识别"` 兜底，不阻塞上传。

> 契约级字段与错误码见 API_CONTRACT / DATABASE_DESIGN，本文件不重复。
