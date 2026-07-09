# Delivery Notes

Status: superseded (API 见 Iteration 07)
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation notes。

## 交付内容

- 列表接口 GET /api/routes：可见性、关键词、标签（any/all）、距离/爬升范围、分页。
- 标签分类接口 GET /api/routes/tag-taxonomy。
- 详情接口 GET /api/routes/{route_id}：元数据、analysis、track（url 指向 /track）、primary_file、actions。
- 列表卡片派生字段：cover_image_url、location、display_tags、track_preview。
- 2026-05-11 UI polish：路线 / 计划 / 候选卡片优先使用上传封面图，回退轨迹 SVG 预览；保存计划详情移除固定 mock 路线 SVG 叠加；列表头不再标注 "real data"；高德路线配色改用相对海拔分桶（坡度配色 helper 保留供后续算法迭代）。

## 测试运行

```text
npm run lint
npm run build
```

后端测试运行记录：历史迭代，未记录。

## 遗留风险

- 地图视觉验证依赖有效的 VITE_AMAP_JS_KEY 和带海拔值的浏览器端数据。
- actions 标志位（can_send_to_trip_plan / can_download_file / can_edit）本轮恒定或仅按归属判断，对应下载 / 编辑 / send-to-trip-plan API 本轮未实现。
- track_preview 当前实现不做高保真压缩（无 Douglas-Peucker / 等距采样 / 点数上限）；高保真 preview 与对象存储 full track 在 Iteration 07 才落地，参见 Iteration 07。

## 对齐与决策

### 2026-05-08

- 本轮仅交付列表 + 详情 + taxonomy，下载 / 编辑 / send-to-trip-plan 推后。
- 详情 track.geojson 恒为 null，完整 geojson 由 /track 端点取得。
- 派生字段 location / display_tags / track_preview 不落库，由 service 计算。

## 暴露的权衡

- 距离 / 爬升指标存于 snapshot 表，无法直接 SQL 过滤，本轮采用"查全量 + 内存过滤 + 手动分页"。
- track_preview 直接复用 track_geojson 坐标，不做压缩，换取实现简单；点数较大的轨迹会增大列表 payload，由 Iteration 07 高保真 preview 修复。
