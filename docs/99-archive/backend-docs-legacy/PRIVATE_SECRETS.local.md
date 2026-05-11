# 本地私有密钥与服务器信息

生成时间：2026-04-29 21:47:58 +08:00

本文档只允许保存在本机开发目录，用于快速重建后端 Demo 环境。不要提交到 Git，不要复制到公开文档，不要在聊天或 Issue 中粘贴真实值。

## 从旧 backend/.env 提取的环境变量

```env
QWEATHER_API_KEY=ef048ac4e8e84540844e7f36da733f76
WEATHER_DEVELOPER_HOST=p25khw5ygp.re
AMAP_API_KEY=0ccf32829c5857a8243d7b5d1d84f63b
LLM_API_KEY=sk-capamwetyjzravoixxlyrianusmcqkumkvacfknmscvepoby
TAVILY_API_KEY=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
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=outdoor_planner
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DATABASE=outdoor_planner
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
JWT_SECRET_KEY=your-secret-key-change-in-production-2024
JWT_ALGORITHM=HS256
JWT_EXPIRE_SECONDS=86400
PROXY_HTTP=http://127.0.0.1:7890
PROXY_HTTPS=http://127.0.0.1:7890
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
API_TIMEOUT=10
API_RETRY=3
API_RATE_LIMIT=30
```

## 从旧 backend/ci-config.yaml 提取的服务器与部署配置

以下内容保留原始部署配置，便于后续重建 CI/CD、服务器登录、部署路径、账号和服务端口。

```yaml
# CI/CD 配置文件（此文件不提交到 git）
# 请填写你的配置信息

# =================== 阿里云镜像仓库 ===================
docker_registry:
  # 镜像仓库地址（地域，如 cn-hangzhou, cn-shanghai）
  region: crpi-zlz2p5f3e8ahmufb.cn-shenzhen.personal.cr.aliyuncs.com
  # 命名空间
  namespace: szhuwai
  # 镜像名称
  image_name: szhuwai
  # 镜像标签（通常为 latest 或从 git 获取）
  image_tag: latest
  # 访问凭证
  username: 14r65t12q
  password: Greedy0805#

# =================== 云服务器 ===================
server:
  # 服务器 IP 或域名
  host: 112.74.107.171
  # SSH 端口
  port: 22
  # 用户名
  username: root
  # 认证方式: ssh_key | password
  auth_type: password
  # SSH 私钥路径（如果使用密钥认证）
  # ssh_key_path: ~/.ssh/id_rsa
  # SSH 密码（如果使用密码认证）
  password: Greedy0805#

# =================== 应用配置 ===================
app:
  # 技术栈
  stack: fastapi
  # 监听端口
  port: 8000
  # 容器名称
  container_name: szhuwai
  # 环境变量（构建时传入）
  env:
    - LOG_LEVEL=INFO
    - PYTHONUNBUFFERED=1

# =================== CI/CD 配置 ===================
cicd:
  # CI 工具: aliyun | github_actions
  provider: aliyun
  # Git 分支触发部署
  branch: main
  # 是否启用自动部署
  auto_deploy: true

```

## 后续处理建议

- Smart_outdoor 正式建仓后，应把本文件加入 .gitignore。
- 生产环境应迁移到服务器环境变量、CI Secret 或密钥管理服务。
- API Client 实现时只读取环境变量，不在代码中硬编码密钥。
