# 部署指南

AI 人物陪伴平台支持两种部署方式：

- **Railway（推荐）**：全托管，免运维，自动扩缩
- **Docker Compose（VPS）**：单台服务器，自管理

---

## 方式一：Railway 一键部署

### 架构

```
Railway 平台
├── Web 服务    (infra/docker/web.Dockerfile)       → 用户端 Next.js
├── API 服务    (infra/docker/backend.Dockerfile)   → FastAPI + Celery Worker（同一容器）
├── PostgreSQL  (Railway 插件)                       → 数据库 + pgvector
└── Redis       (Railway 插件)                       → 缓存 + 队列

外部服务（不在 Railway 上）：
├── LLM API      → OpenAI / DeepSeek / Ollama / vLLM（兼容 OpenAI 协议即可）
├── 视觉模型     → Replicate / DALL-E / SD WebUI
├── 对象存储     → Cloudflare R2（免费 10GB）/ AWS S3
└── 支付         → Stripe
```

### 步骤

#### 1. 准备工作

- [Railway](https://railway.app) 账号（GitHub 登录）
- [Cloudflare R2](https://developers.cloudflare.com/r2/) 存储桶（免费 10GB）
- LLM API Key（OpenAI / DeepSeek / 自托管 Ollama 地址）

#### 2. 在 Railway 创建项目

1. 登录 Railway → New Project → **Deploy from GitHub repo**
2. 选择 `wongdongd/gfriend`
3. Railway 会自动检测到仓库，但需要手动配置两个服务

#### 3. 添加两个服务

Railway 中点击 **+ New Service**，选择同一个 GitHub 仓库，为每个服务配置：

| 服务 | Dockerfile 路径 | 端口 | 最小内存 |
|---|---|---|---|
| **api** | `infra/docker/backend.Dockerfile` | 8000 | 512 MB |
| **web** | `infra/docker/web.Dockerfile` | 3000 | 256 MB |

> API 容器已内置 Celery Worker（通过 entrypoint.sh 同时启动），无需额外的 worker 服务。

> 在 Railway 的 Service Settings → Builder 中，将 **Root Directory** 设为 `/`，**Dockerfile Path** 设为上述路径。

#### 4. 添加 PostgreSQL + Redis 插件

在 Railway 项目 → **New** → **Database** → 分别添加 PostgreSQL 和 Redis。

Railway 会自动注入以下环境变量到所有服务：
- `DATABASE_URL` — PostgreSQL 连接串
- `REDIS_URL` — Redis 连接串

#### 5. 配置环境变量

在 Railway 的 **Variables** 面板（Shared Variables 或每个服务单独设置），添加：

```bash
# === 必需 ===
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_urlsafe(32))">

# === LLM（任选一个，兼容 OpenAI API 协议即可） ===
LLM_PROVIDER=openai          # 或 deepseek / ollama / vllm
LLM_API_KEY=sk-xxxxx
LLM_MODEL=gpt-4o-mini        # 或 deepseek-chat / llama3.1:8b
LLM_BASE_URL=https://api.openai.com/v1   # DeepSeek: https://api.deepseek.com/v1
                                          # Ollama: http://your-gpu-ip:11434/v1

# === 嵌入模型（记忆向量检索） ===
EMBEDDING_PROVIDER=openai
EMBEDDING_API_KEY=<同 LLM_API_KEY>
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536

# === 对象存储（Cloudflare R2） ===
S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
S3_REGION=auto
S3_BUCKET=companion-assets
S3_ACCESS_KEY=<r2-access-key>
S3_SECRET_KEY=<r2-secret-key>

# === 视觉模型（可选，先用 dummy 跑通对话） ===
IMAGE_PROVIDER=dummy         # 或 replicate
IMAGE_API_KEY=

# === 前端（web 服务需要） ===
# API_URL: Web 服务在运行时把 /api/* 代理到后端。Railway 上必须设置，
# 否则回退到 localhost:8000（Web 容器内部）会报 ECONNREFUSED。
# Railway 同项目服务间用内部地址访问，例如：
#   API_URL=http://api.railway.internal:8080     （或使用 API 服务的 RAILWAY_INTERNAL_URL）
NEXT_PUBLIC_API_URL=<Railway API 服务的公开 URL>   # 仅浏览器端需要时使用，代理默认走 API_URL
```

#### 6. 首次部署

Railway 会自动构建并部署。首次启动时，API 服务会自动执行 `alembic upgrade head` 创建数据库表。

检查日志确保无报错后，访问 Web 服务的公开 URL 即可。

---

## 方式二：Docker Compose（VPS 部署）

适合已有 VPS（Hetzner/DigitalOcean/Vultr）的情况。

### 前提

- 服务器：2 vCPU / 4 GB RAM / 50 GB SSD（$20-40/月）
- Ubuntu 22.04 / 24.04
- Docker + Docker Compose 已安装

### 部署

```bash
# 1. 克隆仓库
git clone https://github.com/wongdongd/gfriend.git
cd gfriend

# 2. 配置环境变量
cp .env.example .env
vim .env   # 填入真实密钥

# 3. 启动
docker compose -f infra/docker-compose.prod.yml up -d

# 4. 查看日志
docker compose -f infra/docker-compose.prod.yml logs -f
```

### 添加 HTTPS（后续有域名时）

```bash
# 安装 Nginx + Certbot
apt install nginx certbot python3-certbot-nginx -y

# 配置反向代理（/etc/nginx/sites-available/companion）
server {
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # SSE 流式需要禁用缓冲
        proxy_buffering off;
        proxy_cache off;
    }
}

# 获取证书
certbot --nginx -d your-domain.com
```

---

## LLM 兼容性说明

项目通过适配器模式接入 LLM，任何兼容 OpenAI Chat Completions API 的服务都直接支持：

| 供应商 | LLM_BASE_URL | LLM_MODEL 示例 |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Ollama（自托管） | `http://<gpu-ip>:11434/v1` | `qwen2.5:7b` |
| vLLM（自托管） | `http://<gpu-ip>:8000/v1` | `meta-llama/Llama-3.1-8B` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.1-70b-versatile` |

只需修改 `.env` 中的 `LLM_PROVIDER`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY` 四个变量，不需要改代码。
