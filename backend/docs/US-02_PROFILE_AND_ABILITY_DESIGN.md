# US-02 个人中心与能力画像设计

## 1. 模块定位

US-02 对应底部 Tab：`个人中心`。

个人中心不是普通设置页，它承担两个核心职责：

```text
1. 用户账号与资料管理
知道“这是谁”。

2. 户外能力画像
知道“这个人适合走什么强度的线路”。
```

对产品来说，能力画像是 US-01 Agent 推荐质量的重要输入。

## 2. MVP 边界

MVP 做：

```text
注册
登录
JWT 认证
查看当前用户资料
更新昵称和头像
上传已完成轨迹
生成基础能力画像
查看能力画像
```

MVP 不做：

```text
短信验证码
微信登录
OAuth
refresh token
多设备 session 管理
复杂权限系统
社交关系
勋章系统
公开活动社区
```

## 3. activity_track 与 route_asset 的区别

两者都可能来自 KML / GPX，但业务含义不同。

```text
route_asset
线路资产：我想走 / 我收藏 / 我上传来规划的线路。
用于线路库、搜索、Agent 推荐和转发到出去走走。

activity_track
活动记录：我已经走过 / 我的运动记录 / 用来证明我的能力。
用于能力画像。
```

不能混用的原因：

```text
1. 能力画像污染
用户上传一条想走但没走过的高难路线，如果当作 activity，会错误提高能力判断。

2. 隐私语义不同
用户上传活动记录是为了分析能力，不等于愿意贡献线路资产。

3. UI 心智不同
“线路”里看到的是可规划线路；“个人中心”里看到的是我的完成记录和能力。

4. 扩展字段不同
活动轨迹未来会有完成时间、用时、心率、配速、设备来源；线路资产更关心名称、标签、可见性、推荐、转发规划。
```

MVP 规则：

```text
activity_track 默认不进入线路库。
route_asset 不会自动成为 activity_track。
未来可以支持 activity_track 一键发布为 private/public route_asset，但不进 MVP P0。
```

## 4. 能力画像原则

能力画像只基于用户完成轨迹的客观指标，不分析偏好。

能力画像回答：

```text
你大概能走多远
你大概能爬多少
你近期活动强度如何
你适合什么强度区间
```

能力画像不回答：

```text
你喜欢雪山
你喜欢露营
你喜欢日出
你喜欢哪类风景
```

原因：活动轨迹只能证明能力，不能可靠证明偏好。偏好应来自 US-01 对话中的自然语言表达。

## 5. 数据表设计

US-02 MVP 使用三张表：

```text
users
activity_tracks
user_ability_profiles
```

### 5.1 users

用途：保存用户身份、登录凭证和基础展示资料。

字段：

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 用户 ID。 |
| username | string/null | 登录名，可空，唯一。 |
| phone | string/null | 手机号，可空，唯一。 |
| email | string/null | 邮箱，可空，唯一。 |
| password_hash | string | 密码哈希，不能存明文。 |
| nickname | string | 展示昵称。 |
| avatar_url | string/null | 头像地址。 |
| role | enum/string | `user / admin`。 |
| status | enum/string | `active / disabled`。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |
| last_login_at | datetime/null | 最后登录时间。 |

MVP 登录方式：

```text
用户名/手机号/邮箱 + 密码
```

### 5.2 activity_tracks

用途：保存用户上传的、自己完成过的活动轨迹，用于能力画像。

字段：

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 活动轨迹 ID。 |
| user_id | string/uuid | 所属用户。 |
| file_url | string | 原始 KML / GPX / GeoJSON 文件地址。 |
| file_type | enum/string | `kml / gpx / geojson`。 |
| file_size_bytes | integer/null | 文件大小。 |
| checksum | string/null | 文件哈希。 |
| source_type | enum/string | `manual_upload / watch_import / app_import`。MVP 只实现 `manual_upload`。 |
| activity_date | date/null | 活动发生日期，可空。 |
| distance_km | decimal | 距离。 |
| elevation_gain_m | decimal | 累计爬升。 |
| elevation_loss_m | decimal/null | 累计下降。 |
| elevation_min_m | decimal/null | 最低海拔。 |
| elevation_max_m | decimal/null | 最高海拔。 |
| duration_seconds | integer/null | 总用时，可空。 |
| moving_time_seconds | integer/null | 移动用时，可空。 |
| track_geojson | JSON | 简化轨迹，用于个人中心查看。MVP 可以先不展示，但保留。 |
| analysis_json | JSON | 坡度分布、海拔分布、解析质量等扩展指标。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

### 5.3 user_ability_profiles

用途：保存用户当前能力画像。Agent US-01 推荐时读取这里，而不是每次扫描全部活动轨迹。

字段：

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 能力画像 ID。 |
| user_id | string/uuid | 所属用户。 |
| level | enum/string | `unknown / beginner / normal / strong`。 |
| endurance_score | decimal/null | 耐力评分，0-1。 |
| climb_score | decimal/null | 爬坡能力评分，0-1。 |
| recent_max_distance_km | decimal/null | 近期最大完成距离。 |
| recent_max_elevation_gain_m | decimal/null | 近期最大完成爬升。 |
| activity_count | integer | 已导入活动数量。 |
| confidence | enum/string | `low / medium / high`，无数据时可为 `unknown`。 |
| generated_from_activity_track_ids | JSON | 本次画像基于哪些活动轨迹生成。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

confidence 规则：

```text
activity_count = 0 -> unknown
activity_count = 1 -> low
activity_count 2-4 -> medium
activity_count >= 5 -> high
```

## 6. 能力画像生成规则 MVP

MVP 使用简单、可解释的规则，不上模型。

```text
endurance_score
由近期最大距离、平均距离、活动数量综合得到。

climb_score
由近期最大爬升、平均爬升、活动数量综合得到。

level
由 endurance_score 和 climb_score 得到。

confidence
由 activity_count 得到。
```

示例：

```json
{
  "level": "normal",
  "endurance_score": 0.62,
  "climb_score": 0.58,
  "recent_max_distance_km": 18.0,
  "recent_max_elevation_gain_m": 1200,
  "activity_count": 1,
  "confidence": "low"
}
```

画像提示文案：

```text
当前画像基于 1 条完成轨迹，可信度较低。多导入几条后，推荐会更准确。
```

## 7. JWT 认证设计

MVP 认证采用 JWT Token。

规则：

```text
注册后生成用户。
登录成功后返回 access_token。
前端后续请求在 Authorization Header 中携带 Bearer Token。
后端通过 Token 解析当前用户。
```

登录返回：

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "username": "outdoor_user",
    "nickname": "山野用户",
    "avatar_url": null,
    "role": "user"
  }
}
```

请求 Header：

```http
Authorization: Bearer jwt_token
```

JWT Payload：

```json
{
  "sub": "user_123",
  "role": "user",
  "exp": 1770000000
}
```

安全底线：

```text
password_hash 必须哈希，不能存明文。
JWT_SECRET_KEY 从环境变量读取。
access_token 设置过期时间。
```

## 8. API 契约

US-02 MVP API 共 6 个：

```text
1. POST /api/auth/register
2. POST /api/auth/login
3. GET /api/me
4. PATCH /api/me
5. POST /api/me/activity-tracks/upload
6. GET /api/me/ability-profile
```

### 8.1 POST /api/auth/register

用途：注册用户。

Request：

```json
{
  "username": "outdoor_user",
  "phone": null,
  "email": "user@example.com",
  "password": "plain_password",
  "nickname": "山野用户"
}
```

Response：

```json
{
  "user": {
    "id": "user_123",
    "username": "outdoor_user",
    "nickname": "山野用户",
    "avatar_url": null,
    "role": "user"
  }
}
```

规则：

```text
username / phone / email 至少一个存在。
password 不能明文入库，只保存 password_hash。
```

### 8.2 POST /api/auth/login

用途：用户登录。

Request：

```json
{
  "account": "outdoor_user",
  "password": "plain_password"
}
```

`account` 可以是：

```text
username
phone
email
```

Response：

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "username": "outdoor_user",
    "nickname": "山野用户",
    "avatar_url": null,
    "role": "user"
  }
}
```

### 8.3 GET /api/me

用途：获取当前用户资料。

Header：

```http
Authorization: Bearer jwt_token
```

Response：

```json
{
  "id": "user_123",
  "username": "outdoor_user",
  "phone": null,
  "email": "user@example.com",
  "nickname": "山野用户",
  "avatar_url": null,
  "role": "user",
  "status": "active",
  "created_at": "2026-05-05T12:00:00Z",
  "last_login_at": "2026-05-05T12:10:00Z"
}
```

### 8.4 PATCH /api/me

用途：更新当前用户资料。

Request：

```json
{
  "nickname": "雪山徒步者",
  "avatar_url": "https://cdn.example.com/avatar.jpg"
}
```

MVP 只允许更新：

```text
nickname
avatar_url
```

### 8.5 POST /api/me/activity-tracks/upload

用途：上传用户自己完成过的 KML / GPX / GeoJSON 轨迹，用于生成或更新能力画像。

注意：这是 `activity_track`，不是 `route_asset`，不会自动进入线路库。

Request：

```text
multipart/form-data
```

字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| file | file | 是 | KML / GPX / GeoJSON 文件。 |
| activity_date | date/null | 否 | 活动日期。 |
| source_type | string | 否 | MVP 固定 `manual_upload`。 |

Response：

```json
{
  "activity_track_id": "act_123",
  "parse_status": "parsed",
  "analysis": {
    "distance_km": 18.0,
    "elevation_gain_m": 1200,
    "elevation_loss_m": 1200,
    "elevation_min_m": 2600,
    "elevation_max_m": 3900
  },
  "ability_profile": {
    "level": "normal",
    "endurance_score": 0.62,
    "climb_score": 0.58,
    "recent_max_distance_km": 18.0,
    "recent_max_elevation_gain_m": 1200,
    "activity_count": 1,
    "confidence": "low"
  }
}
```

### 8.6 GET /api/me/ability-profile

用途：获取当前用户能力画像。

Response：

```json
{
  "level": "normal",
  "endurance_score": 0.62,
  "climb_score": 0.58,
  "recent_max_distance_km": 18.0,
  "recent_max_elevation_gain_m": 1200,
  "activity_count": 1,
  "confidence": "low",
  "message": "当前画像基于 1 条完成轨迹，可信度较低。多导入几条后，推荐会更准确。"
}
```

## 9. 与 US-01 的关系

US-01 AgentRun 输入上下文包含：

```text
user_ability_profile
```

如果用户没有上传完成轨迹：

```text
user_ability_profile = null
```

Agent 使用 `context_state.ability_hint`；如果仍然缺失，则自然追问用户体能情况。

如果用户已生成能力画像，Agent 可使用：

```text
level
endurance_score
climb_score
recent_max_distance_km
recent_max_elevation_gain_m
confidence
```

用于线路推荐中的能力匹配和风险判断。
