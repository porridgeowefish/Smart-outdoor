下面是从 API / 数据库设计之后，目前应该保留的 Mermaid 图。

**1. US-01 API 主流程**

```mermaid
sequenceDiagram
    actor User as 用户
    participant FE as 前端
    participant API as TripPlan API
    participant Agent as Agent Workflow
    participant DB as Database
    participant SSE as SSE Events

    User->>FE: 输入自然语言需求
    FE->>API: POST /api/trip-plans/messages
    API->>DB: 创建/更新 trip_plan
    API->>DB: 写入 trip_plan_messages(user)
    API->>DB: 创建 agent_run
    API-->>FE: trip_plan_id / message_id / agent_run_id

    FE->>SSE: GET /api/agent-runs/{agent_run_id}/events
    Agent->>DB: 读取 trip_plan / messages / ability_profile
    Agent->>DB: 更新 context_summary / context_state
    Agent->>SSE: run.phase_changed
    Agent->>SSE: message.delta

    alt 信息不足
        Agent->>SSE: run.waiting_user
        Agent->>DB: agent_run.status = waiting_user
    else 信息充分
        Agent->>DB: 读取 route_assets / route_analysis_snapshots
        Agent->>DB: 写入 trip_plan_candidate_routes
        Agent->>SSE: candidate_routes.updated
        Agent->>SSE: run.completed
    end

    User->>FE: 点击候选卡片
    FE->>API: GET /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}
    API->>DB: 查询 candidate + route + analysis
    API-->>FE: 候选详情

    User->>FE: 保存到我的规划
    FE->>API: POST /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save
    API->>DB: 创建 route_plan_snapshot
    API-->>FE: snapshot_id
```

**2. US-01 / US-02 / US-03 ER 图**

```mermaid
erDiagram
    USERS ||--o{ TRIP_PLANS : owns
    USERS ||--o{ ROUTE_ASSETS : creates
    USERS ||--o{ ROUTE_FILES : uploads
    USERS ||--o{ ROUTE_PLAN_SNAPSHOTS : saves
    USERS ||--o{ ACTIVITY_TRACKS : uploads
    USERS ||--o| USER_ABILITY_PROFILES : has

    TRIP_PLANS ||--o{ TRIP_PLAN_MESSAGES : contains
    TRIP_PLANS ||--o{ AGENT_RUNS : triggers
    TRIP_PLANS ||--o{ TRIP_PLAN_CANDIDATE_ROUTES : has
    TRIP_PLANS ||--o{ ROUTE_PLAN_SNAPSHOTS : produces

    AGENT_RUNS ||--o{ TRIP_PLAN_CANDIDATE_ROUTES : recommends
    AGENT_RUNS ||--o{ TRIP_PLAN_MESSAGES : generates

    ROUTE_ASSETS ||--o{ ROUTE_FILES : has
    ROUTE_ASSETS ||--o{ ROUTE_ANALYSIS_SNAPSHOTS : analyzed_as
    ROUTE_ASSETS ||--o{ TRIP_PLAN_CANDIDATE_ROUTES : referenced_by
    ROUTE_ASSETS ||--o{ ROUTE_PLAN_SNAPSHOTS : saved_as

    ROUTE_FILES ||--o{ ROUTE_ANALYSIS_SNAPSHOTS : produces
    ROUTE_ANALYSIS_SNAPSHOTS ||--o{ TRIP_PLAN_CANDIDATE_ROUTES : used_by
    ROUTE_ANALYSIS_SNAPSHOTS ||--o{ ROUTE_PLAN_SNAPSHOTS : frozen_in

    TRIP_PLAN_CANDIDATE_ROUTES ||--o| ROUTE_PLAN_SNAPSHOTS : saved_once_as

    USERS {
        string id PK
        string username
        string phone
        string email
        string password_hash
        string nickname
        string avatar_url
        string role
        string status
        datetime created_at
        datetime updated_at
        datetime last_login_at
    }

    TRIP_PLANS {
        string id PK
        string user_id FK
        string title
        string status
        text context_summary
        json context_state
        datetime created_at
        datetime updated_at
        datetime closed_at
    }

    TRIP_PLAN_MESSAGES {
        string id PK
        string trip_plan_id FK
        string agent_run_id FK
        string role
        text content
        string content_type
        datetime created_at
    }

    AGENT_RUNS {
        string id PK
        string trip_plan_id FK
        string trigger_message_id FK
        string run_status
        string phase
        string error_code
        text error_message
        datetime started_at
        datetime completed_at
        datetime created_at
        datetime updated_at
    }

    ROUTE_ASSETS {
        string id PK
        string name
        text description
        string cover_image_url
        json manual_tags
        string source_type
        string source_name
        string visibility
        string status
        string created_by_user_id FK
        datetime created_at
        datetime updated_at
    }

    ROUTE_FILES {
        string id PK
        string route_asset_id FK
        string file_url
        string file_type
        int file_size_bytes
        string checksum
        string uploaded_by_user_id FK
        string parse_status
        text parse_error
        datetime created_at
        datetime updated_at
    }

    ROUTE_ANALYSIS_SNAPSHOTS {
        string id PK
        string route_asset_id FK
        string route_file_id FK
        decimal distance_km
        decimal elevation_gain_m
        decimal elevation_loss_m
        decimal elevation_min_m
        decimal elevation_max_m
        decimal climb_ratio
        decimal steep_ratio
        json start_point
        json end_point
        json bounds
        json center_point
        json track_geojson
        json analysis_json
        datetime created_at
    }

    TRIP_PLAN_CANDIDATE_ROUTES {
        string id PK
        string trip_plan_id FK
        string agent_run_id FK
        string route_asset_id FK
        string route_analysis_snapshot_id FK
        int rank
        json advantage_tags
        text recommendation_reason
        json score_breakdown
        datetime created_at
    }

    ROUTE_PLAN_SNAPSHOTS {
        string id PK
        string user_id FK
        string trip_plan_id FK
        string candidate_route_id FK
        string route_asset_id FK
        string route_analysis_snapshot_id FK
        string title
        string cover_image_url
        json route_summary
        json planning_detail
        json evidence
        text share_text
        text user_note
        datetime saved_at
        datetime created_at
        datetime updated_at
    }

    ACTIVITY_TRACKS {
        string id PK
        string user_id FK
        string file_url
        string file_type
        int file_size_bytes
        string checksum
        string source_type
        date activity_date
        decimal distance_km
        decimal elevation_gain_m
        decimal elevation_loss_m
        decimal elevation_min_m
        decimal elevation_max_m
        int duration_seconds
        int moving_time_seconds
        json track_geojson
        json analysis_json
        datetime created_at
        datetime updated_at
    }

    USER_ABILITY_PROFILES {
        string id PK
        string user_id FK
        string level
        decimal endurance_score
        decimal climb_score
        decimal recent_max_distance_km
        decimal recent_max_elevation_gain_m
        int activity_count
        string confidence
        json generated_from_activity_track_ids
        datetime created_at
        datetime updated_at
    }
```

**3. US-01 Agent Workflow**

```mermaid
flowchart TD
    A["用户发送消息"] --> B["创建 AgentRun"]
    B --> C["加载输入上下文<br/>trip_plan / context_summary / context_state<br/>recent_messages / current_user_message / ability_profile"]

    C --> D["intent_detection<br/>识别本轮意图"]
    D --> E["context_update<br/>更新 context_summary 与 context_state"]
    E --> F["sufficiency_check<br/>信息充分度判断"]

    F -->|信息不足| G["response_generation<br/>生成自然追问"]
    G --> H["SSE: message.delta / message.completed"]
    H --> I["SSE: run.waiting_user<br/>动态问题 + 最多 3 个选项"]
    I --> J["agent_runs.run_status = waiting_user"]

    F -->|信息充分| K["route_retrieval<br/>四层轻量召回"]
    K --> K1["硬约束过滤<br/>public / active / 有分析快照"]
    K1 --> K2["能力与轨迹指标匹配<br/>距离 / 爬升 / 海拔 / 陡坡比"]
    K2 --> K3["语义与偏好召回<br/>目标 / 景观 / 体验"]
    K3 --> K4["重排得到 top 10 候选池"]

    K4 --> L["evidence_search<br/>API 证据优先，Web 只补充"]
    L --> L1["天气<br/>QWeather primary<br/>fallback: AMap Weather"]
    L --> L2["交通<br/>AMap driving / transit"]
    L --> L3["Web 搜索<br/>Tavily 开放网页<br/>小红书不作为可靠源"]

    L1 --> M["plan_evaluation<br/>高分 + 差异化优势 + 证据约束"]
    L2 --> M
    L3 --> M

    M --> M1["选择 3 条候选<br/>稳妥型 / 目标最匹配型 / 差异化备选型"]
    M1 --> M2["写入 trip_plan_candidate_routes<br/>rank / tags / reason / score_breakdown"]

    M2 --> N["evaluator<br/>防幻觉审稿人"]
    N --> N1{"是否存在无证据断言<br/>或安全风险遗漏？"}

    N1 -->|是| N2["降级表达<br/>未确认 / 证据不足 / 出发前核实"]
    N1 -->|否| O["response_generation<br/>生成最终回复"]

    N2 --> O
    O --> P["写入 trip_plan_messages<br/>role = assistant"]
    P --> Q["SSE: message.delta / message.completed"]
    Q --> R["SSE: candidate_routes.updated"]
    R --> S["SSE: run.completed"]

    L -->|部分证据失败但可推荐| T["agent_runs.run_status = partial"]
    K -->|候选为空| U["agent_runs.run_status = failed"]
    U --> V["SSE: run.failed"]

    S --> W["agent_runs.run_status = succeeded"]
```

**4. US-03 线路上传与解析流程**

```mermaid
flowchart TD
    A["用户进入线路 Tab"] --> B["点击上传轨迹"]
    B --> C["选择 KML / GPX / GeoJSON 文件"]
    C --> D["填写线路名称 / 描述 / visibility"]
    D --> E["选择 manual_tags<br/>补给 / 交通 / 安全 / 通信 / 路况 / 风景"]
    E --> F["POST /api/routes/upload<br/>multipart/form-data"]

    F --> G["创建 route_assets<br/>保存 name / visibility / manual_tags"]
    G --> H["保存原始文件<br/>写 route_files"]
    H --> I["同步解析轨迹"]

    I --> J{"解析是否成功？"}

    J -->|成功| K["生成 route_analysis_snapshots"]
    K --> K1["距离 / 爬升 / 海拔 / 坡度"]
    K --> K2["start_point / end_point / bounds / center_point"]
    K --> K3["track_geojson<br/>简化轨迹用于地图渲染"]
    K3 --> L["route_files.parse_status = parsed"]
    L --> M["返回 route_id / file_id / parse_status=parsed"]

    J -->|失败| N["route_files.parse_status = failed"]
    N --> O["返回 TRACK_PARSE_FAILED"]
```

**5. US-03 线路详情与转发规划**

```mermaid
flowchart TD
    A["用户进入线路 Tab"] --> B["GET /api/routes<br/>线路列表 / 搜索 / 标签筛选"]
    B --> C["展示线路卡片<br/>小图 / 名称 / 距离 / 爬升 / 标签"]
    C --> D["用户点击线路卡片"]

    D --> E["GET /api/routes/{route_id}"]
    E --> F["返回线路详情"]
    F --> F1["route_assets<br/>名称 / 描述 / manual_tags"]
    F --> F2["route_analysis_snapshots<br/>距离 / 爬升 / 海拔 / track_geojson"]
    F --> F3["route_files<br/>primary_file 原始文件"]

    F2 --> G["前端地图渲染 track.geojson"]

    F --> H["用户点击转发到出去走走"]
    H --> I["POST /api/routes/{route_id}/send-to-trip-plan"]

    I --> J{"是否传入 trip_plan_id？"}
    J -->|否| K["创建新 trip_plan"]
    J -->|是| L["追加到已有 trip_plan"]

    K --> M["写入用户意图消息"]
    L --> M
    M --> N["context_state.seed_route = route_id"]
    N --> O["创建 agent_run"]
    O --> P["跳转出去走走聊天页"]
    P --> Q["订阅 SSE<br/>GET /api/agent-runs/{agent_run_id}/events"]
```

**6. US-02 个人中心与能力画像**

```mermaid
flowchart TD
    A["用户进入个人中心"] --> B["GET /api/me<br/>获取用户资料"]
    A --> C["GET /api/me/ability-profile<br/>获取能力画像"]

    C --> D{"是否已有能力画像？"}

    D -->|没有| E["展示引导<br/>上传已完成轨迹以生成能力画像"]
    D -->|有| F["展示能力画像<br/>耐力 / 爬坡 / 最大距离 / 最大爬升 / 可信度"]

    E --> G["用户上传已完成轨迹"]
    G --> H["POST /api/me/activity-tracks/upload<br/>KML / GPX / GeoJSON"]

    H --> I["保存 activity_tracks"]
    I --> J["解析轨迹指标<br/>距离 / 爬升 / 海拔 / track_geojson"]
    J --> K["更新 user_ability_profiles"]

    K --> L["返回 ability_profile"]
    L --> F

    F --> M["US-01 AgentRun 读取 user_ability_profile"]
    M --> N["用于能力匹配和风险判断"]
```

**7. Mock / Real 契约驱动对接**

```mermaid
flowchart TD
    A["后端 Pydantic Request/Response"] --> B["FastAPI 生成 /openapi.json"]
    B --> C["前端 openapi-typescript 生成 TS 类型"]
    C --> D["前端 API Client"]
    C --> E["MSW Mock Handlers"]

    F{"VITE_USE_MOCK_API ?"} -->|true| E
    F -->|false| D

    E --> G["返回符合 OpenAPI 类型的 mock response"]
    D --> H["请求真实后端 /api"]

    H --> I["真实 Response 由 Pydantic 保证"]
    G --> J["页面组件"]
    I --> J

    J --> K["页面代码不关心 mock / real"]
```