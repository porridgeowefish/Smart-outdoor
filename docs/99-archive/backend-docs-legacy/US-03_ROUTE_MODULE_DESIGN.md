# US-03 线路模块设计：线路搜索、上传、详情与转发规划

## 1. 模块定位

US-03 对应底部 Tab：`线路`。

它负责线路资产的浏览、搜索、上传、轨迹渲染和转发到“出去走走”进行 Agent 规划。

US-03 是 US-01 的数据基础。Agent 推荐不是凭空生成，而是从 `route_assets + route_analysis_snapshots + manual_tags` 中召回候选线路。

## 2. 核心闭环

```text
用户进入“线路”
↓
浏览 / 搜索线路卡片
↓
点击线路卡片
↓
查看线路本体详情和轨迹地图
↓
可上传 KML / GPX / GeoJSON
↓
可把某条线路转发到“出去走走”做规划
```

## 3. 可见性规则

线路 Tab 默认展示：

```text
public 线路
+
当前用户自己的 private 线路
```

规则：

```text
public
所有用户可见，可进入线路搜索结果，可被 Agent 默认推荐。

private
仅创建者自己可见，线路 Tab 中可展示“私人”标记。

Agent 默认推荐池
只使用 public。

用户主动把 private 线路转发到“出去走走”
Agent 可以基于这条 private 线路做规划。
```

## 4. 手动标签体系

导入轨迹时，用户可以为线路补充手动标签。标签是线路资产的补充语义信息，用于弥补 KML / GPX 无法解析的经验信息。

KML / GPX 可以解析：

```text
距离
爬升
海拔
坡度
轨迹形状
```

但无法可靠解析：

```text
补给
通信
撤退点
路况
风景
适合人群
```

因此手动标签进入 `route_assets.manual_tags JSON`。

### 4.1 标签分类

每一类都可以多选。

#### 补给服务

```text
有小卖部
有饮用水
有餐饮点
无补给
装备租赁
```

#### 交通设施

```text
停车场
公交站
自驾友好
摆渡车
```

#### 安全与撤退

```text
有撤退点
沿途可撤
无明显撤退点
有路标
无路标
```

#### 通信状态

```text
基本有信号
部分信号弱
无信号
```

#### 路况与地形

```text
铺装路
石板路
土路/机耕道
碎石路
泥泞路
野路
冰雪路
```

#### 风光与场景

```text
森林
溪流
河流
海子
日出
日落
雪山
古镇
牧场
花海
亲子友好
露营友好
```

### 4.2 manual_tags 示例

```json
{
  "supply": ["有饮用水", "有餐饮点"],
  "transport": ["停车场", "自驾友好"],
  "safety": ["沿途可撤", "有路标"],
  "signal": ["部分信号弱"],
  "terrain": ["碎石路", "泥泞路"],
  "scenery": ["雪山", "海子", "日出"]
}
```

### 4.3 设计边界

```text
manual_tags 不能替代轨迹指标。
manual_tags 不能替代外部证据。
manual_tags 不能证明近期路况。
```

它主要用于：

```text
线路详情展示
线路搜索筛选
Agent route_retrieval 的语义/偏好召回
plan_evaluation 生成优势标签
```

## 5. 原始文件与渲染轨迹

原始 KML / GPX / GeoJSON 仍然保存，但日常展示和推荐使用解析后的派生数据。

分工：

```text
route_files
保存原始 KML / GPX / GeoJSON 文件。

route_analysis_snapshots.track_geojson
保存简化后的轨迹 GeoJSON，用于前端地图渲染。

route_analysis_snapshots 指标字段
保存距离、爬升、海拔、坡度、陡坡比等，用于筛选、推荐和详情展示。
```

为什么原始文件还要存：

```text
可追溯
可下载
算法升级后可重新解析
数据纠错
后续多格式支持
```

为什么日常不用原始文件：

```text
前端解析 KML/GPX 麻烦
移动端性能不稳定
文件质量不可控
推荐系统需要结构化指标，不需要原始文件
地图渲染更适合简化 GeoJSON
```

MVP 数据流：

```text
上传 KML/GPX/GeoJSON
↓
保存到 route_files.file_url
↓
解析生成：
  distance_km
  elevation_gain_m
  start_point
  end_point
  bounds
  center_point
  track_geojson
↓
写入 route_analysis_snapshots
↓
页面展示和 Agent 推荐都读 route_analysis_snapshots
```

## 6. GET /api/routes

### 用途

获取线路列表 / 搜索线路 / 标签筛选。

默认返回：

```text
public 线路 + 当前用户自己的 private 线路
```

### Query

| 参数 | 默认值 | 说明 |
|---|---:|---|
| keyword | 空 | 搜索关键词，可空。 |
| visibility | all | `public / private / all`。 |
| min_distance_km | 空 | 最小距离。 |
| max_distance_km | 空 | 最大距离。 |
| min_elevation_gain_m | 空 | 最小爬升。 |
| max_elevation_gain_m | 空 | 最大爬升。 |
| tags | 空 | 多选标签，多个用逗号分隔。 |
| tag_match_mode | any | `any / all`。 |
| page | 1 | 页码。 |
| page_size | 20 | 每页数量。 |

示例：

```http
GET /api/routes?keyword=雪山&tags=雪山,自驾友好,有饮用水&tag_match_mode=any&page=1&page_size=20
```

### Response

```json
{
  "items": [
    {
      "route_id": "route_1",
      "name": "四姑娘山大峰",
      "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
      "visibility": "public",
      "distance_km": 15.2,
      "elevation_gain_m": 1320,
      "manual_tags": {
        "supply": ["有饮用水"],
        "transport": ["停车场", "自驾友好"],
        "safety": ["沿途可撤"],
        "signal": ["部分信号弱"],
        "terrain": ["碎石路"],
        "scenery": ["雪山", "日出"]
      },
      "display_tags": ["雪山", "自驾友好", "有饮用水"]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### 卡片展示字段

```text
cover_image_url
name
distance_km
elevation_gain_m
display_tags
```

`display_tags` 是后端为卡片挑出的 2-3 个展示标签，来源于 `manual_tags + analysis_json`。

## 7. GET /api/routes/{route_id}

### 用途

查看线路本体详情。

注意：这是线路库详情，不是 Agent 规划详情。

展示：

```text
线路自己的客观信息
用户导入时补充的标签
轨迹解析指标
简化 GeoJSON 轨迹
原始文件信息
```

不展示：

```text
为什么适合你
本次规划建议
预算
装备建议
本次天气/交通判断
```

### Response

```json
{
  "route_id": "route_1",
  "name": "四姑娘山大峰",
  "description": "经典雪山体验路线，强度较高。",
  "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
  "visibility": "public",
  "source_type": "system",
  "source_name": "管理员导入",
  "manual_tags": {
    "supply": ["有饮用水"],
    "transport": ["停车场", "自驾友好"],
    "safety": ["沿途可撤", "有路标"],
    "signal": ["部分信号弱"],
    "terrain": ["碎石路"],
    "scenery": ["雪山", "日出"]
  },
  "analysis": {
    "route_analysis_snapshot_id": "analysis_1",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "elevation_loss_m": 1320,
    "elevation_min_m": 3200,
    "elevation_max_m": 5025,
    "climb_ratio": 86.8,
    "steep_ratio": 0.18,
    "start_point": {"name":"海子沟入口","lon":102.9,"lat":31.0},
    "end_point": {"name":"海子沟入口","lon":102.9,"lat":31.0},
    "bounds": {},
    "center_point": {},
    "analysis_json": {}
  },
  "track": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "simplified": true,
    "point_count": 842,
    "geojson": {
      "type": "LineString",
      "coordinates": [
        [102.9, 31.0],
        [102.91, 31.01]
      ]
    }
  },
  "primary_file": {
    "file_id": "file_1",
    "file_type": "gpx",
    "file_url": "https://cdn.example.com/routes/file_1.gpx",
    "parse_status": "parsed"
  },
  "actions": {
    "can_send_to_trip_plan": true,
    "can_download_file": false,
    "can_edit": false
  }
}
```

### 页面展示结构

```text
顶部：图片 / 名称 / visibility 标记
核心指标：距离 / 爬升 / 海拔 / 陡坡比
地图：track.geojson 轨迹渲染
标签：补给 / 交通 / 安全 / 通信 / 路况 / 风景
文件：原始 KML / GPX 信息
底部操作：转发到出去走走
```

### 权限规则

```text
public
所有登录用户可查看。

private
只有 created_by_user_id 本人可查看。

can_edit
只有创建者或管理员为 true。
```

### 设计边界

这个接口不调用 Agent，不查天气，不查交通。

如果用户想基于这条线路做规划，点击“转发到出去走走”。

## 8. POST /api/routes/upload

### 用途

用户上传 KML / GPX / GeoJSON，补充路线名称、描述、可见性、手动标签，系统解析后生成线路资产。

### Request

使用：

```text
multipart/form-data
```

含义：一次请求里同时上传文件和普通字段。

字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| file | file | 是 | KML / GPX / GeoJSON 文件。 |
| name | string | 是 | 线路名称。 |
| description | string | 否 | 线路简介。 |
| visibility | string | 否 | `public / private`，默认 `private`。 |
| manual_tags | JSON string | 否 | 用户多选标签。 |

示例：

```text
file = route.gpx
name = 蛇海子穿越白海子
description = 高山海子穿越路线
visibility = private
manual_tags = {
  "supply": ["无补给"],
  "transport": ["自驾友好"],
  "safety": ["无明显撤退点", "无路标"],
  "signal": ["无信号"],
  "terrain": ["野路", "碎石路"],
  "scenery": ["雪山", "海子"]
}
```

### Response

MVP 同步解析，成功返回：

```json
{
  "route_id": "route_123",
  "file_id": "file_123",
  "parse_status": "parsed"
}
```

失败返回：

```json
{
  "route_id": "route_123",
  "file_id": "file_123",
  "parse_status": "failed",
  "parse_error": "轨迹解析失败，请检查文件格式"
}
```

### parse_status

```text
pending
已上传，等待解析。MVP 暂不主用，未来后台解析使用。

parsed
解析成功，已经生成 route_analysis_snapshot。

failed
解析失败，文件格式或内容有问题。
```

### MVP 与未来取舍

MVP：

```text
上传接口同步解析。
成功返回 parse_status = parsed。
失败返回 parse_status = failed 或错误码。
```

未来：

```text
可迁移到后台 Worker。
上传后先返回 pending。
前端轮询或订阅解析状态。
```

### 落库流程

```text
1. 创建 route_assets
2. 保存原始文件到本地或对象存储
3. 创建 route_files
4. 解析轨迹
5. 创建 route_analysis_snapshots
6. 更新 route_files.parse_status
```

### 错误码

```json
{"code":"UNSUPPORTED_FILE_TYPE","message":"仅支持 KML、GPX、GeoJSON 文件"}
```

```json
{"code":"TRACK_PARSE_FAILED","message":"轨迹解析失败，请检查文件格式"}
```

## 9. POST /api/routes/{route_id}/send-to-trip-plan

### 用途

用户在线路详情页点击“转发到出去走走”，把这条线路带入 Agent 对话，让 Agent 基于这条线路做规划。

### 核心交互

```text
用户在线路详情页看到某条线路
↓
点击“转发到出去走走”
↓
系统创建或追加 trip_plan
↓
向 trip_plan 写入一条用户意图消息
↓
创建 agent_run
↓
前端跳转到出去走走聊天页
↓
建立 SSE 流式连接
```

### Request

```json
{
  "trip_plan_id": null,
  "user_note": "我想看看这条线周末一天能不能走",
  "client_context": {
    "timezone": "Asia/Shanghai",
    "locale": "zh-CN"
  }
}
```

字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| trip_plan_id | string/null | 否 | 为空表示创建新对话；非空表示追加到已有对话。 |
| user_note | string/null | 否 | 用户补充说明。 |
| client_context | object | 否 | 客户端时区和语言。 |

### Response

```json
{
  "trip_plan_id": "tp_123",
  "message_id": "msg_456",
  "agent_run_id": "run_789",
  "run_status": "queued"
}
```

返回结构与 `POST /api/trip-plans/messages` 一致。

### 系统生成的用户消息

如果用户填写 `user_note`：

```text
我想基于线路「蛇海子穿越白海子」做规划：我想看看这条线周末一天能不能走
```

如果用户没填：

```text
我想基于线路「蛇海子穿越白海子」做规划
```

### context_state 预填

后端可以预填：

```json
{
  "seed_route": {
    "route_id": "route_123",
    "name": "蛇海子穿越白海子"
  }
}
```

Agent 后续基于这条线路做：

```text
天气
交通
风险
能力匹配
是否适合当前时间
```

### 权限规则

```text
public route
所有登录用户可转发。

private route
只有创建者本人可转发。
```

### 设计边界

这个接口不直接生成 snapshot。它只是把线路送进一次 `trip_plan` 对话。后续仍由 Agent 决定追问、评估、生成详情和保存到我的规划。

## 10. 数据库同步变更

### route_assets 增加字段

```text
manual_tags JSON
```

用途：保存用户导入轨迹时补充的多选标签。

### route_analysis_snapshots 增加字段

```text
track_geojson JSON
```

用途：保存简化后的 GeoJSON 轨迹，用于移动端地图渲染。

## 11. 与 US-01 的关系

US-03 提供线路资产：

```text
route_assets
route_files
route_analysis_snapshots
manual_tags
track_geojson
```

US-01 Agent 使用这些资产进行：

```text
route_retrieval
plan_evaluation
候选卡片生成
候选详情生成
```

用户也可以主动从线路详情转发到“出去走走”，让 Agent 基于指定线路做规划。
