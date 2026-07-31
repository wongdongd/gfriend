# AI 人物陪伴平台

> 让用户亲手创作、培养并与之长期相处的 AI 人物陪伴产品。以文字对话为核心，通过 AI 图片和短视频让人物"看得见"、拥有更强的陪伴感。

## 技术栈

| 层级 | 技术 | 说明 |
|---|---|---|
| 前端 | Next.js 15 · TypeScript · Tailwind CSS · shadcn/ui | 用户端 + 管理后台（`/admin`） |
| API | FastAPI · Uvicorn · Pydantic v2 | 领域 API、SSE 流式、鉴权 |
| Worker | Celery · Redis | 图片/视频/审核异步队列 |
| 数据库 | PostgreSQL 16 · SQLAlchemy 2.0 · Alembic | 含 `pgvector` 扩展用于记忆检索 |
| 缓存/队列 | Redis | 限流、Celery broker、会话缓存 |
| 对象存储 | S3 兼容（MinIO 本地） | 角色参考图、生成作品、短期签名 URL |
| 适配器 | LLM / 视觉 / 支付 / 存储 | 供应商可替换，统一抽象基类 |

## 目录结构

```text
apps/
  web/                # Next.js 用户端 + 管理后台
backend/              # Python 后端项目（直接 python main.py 启动，非可安装包）
  main.py             # 统一入口：api / worker / migrate
  shared/             # 配置、数据库会话、安全、依赖注入、通用工具
  db/                 # SQLAlchemy models + Alembic 迁移
  companion_core/     # 上下文组装 / 记忆检索 / 安全编排
  provider_adapters/  # LLM / 视觉 / 支付 / 存储 适配器
  api/                # FastAPI 主服务（routers / core）
  worker/             # Celery Worker（tasks / celery_app）
  alembic.ini
  pyproject.toml      # 工具配置（ruff/mypy/pytest），依赖见 requirements.txt
  requirements.txt
packages/
  shared/             # 前端共享 TypeScript 类型/常量
infra/
  docker/             # Dockerfile（backend / web）
  docker-compose.yml  # PostgreSQL + Redis + MinIO + 全栈
docs/                 # 产品方案、实现方案与设计文档
```

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 20+、pnpm 9+
- Docker & Docker Compose（用于本地 PostgreSQL / Redis / MinIO）

### 1. 启动基础设施

```bash
cp .env.example .env          # 填入必要的密钥
docker compose -f infra/docker-compose.yml up -d postgres redis minio
```

### 2. 启动后端 API

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py migrate           # 执行数据库迁移
python main.py                   # 启动 API（默认），等价于 python main.py api
```

### 3. 启动 Worker

```bash
cd backend
source .venv/bin/activate        # 激活上面的同一虚拟环境
python main.py worker            # 启动 Celery Worker
```

### 4. 启动前端

```bash
cd apps/web
pnpm install
pnpm dev                       # http://localhost:3000
```

## 文档

- [产品方案](docs/01-mvp-product-plan.md)
- [原始实现方案](docs/02-mvp-implementation-plan.md)
- [Python 后端实现方案](docs/03-python-implementation-plan.md)
- [部署指南](docs/deployment.md) ← **Railway 一键部署 / Docker Compose VPS 部署**

## 部署

推荐 **Railway**（全托管，免运维）。详见 [docs/deployment.md](docs/deployment.md)。

### 30 秒部署到 Railway

1. Fork 本仓库到你的 GitHub
2. 在 [Railway](https://railway.app) 中 New Project → Deploy from GitHub
3. 添加三个服务（api / worker / web），Dockerfile 路径见部署文档
4. 添加 PostgreSQL + Redis 插件
5. 设置 `SECRET_KEY` + `LLM_API_KEY` 环境变量
6. 完成！访问 Web 服务的公开 URL

### 自托管模型

任何兼容 OpenAI Chat Completions API 的模型服务都直接支持。修改环境变量即可：

```bash
LLM_BASE_URL=http://your-gpu:11434/v1   # Ollama
LLM_MODEL=qwen2.5:7b
```

## 开发阶段

- **阶段 A · 陪伴闭环**：邮箱/OAuth 登录、模板化角色创建、文本聊天、会话历史、显式记忆卡片、角色主页、基础安全。
- **阶段 B · 视觉陪伴**：角色视觉设定、场景/风格模板、图片任务队列、作品时间线、积分冻结与失败补偿。
- **阶段 C · 商业化与视频**：Stripe 支付、订阅权益、视频生成、完整管理后台、监控告警。

## 许可

UNLICENSED
