# AI 人物陪伴平台：Python 后端实现方案

本方案以 `01-mvp-product-plan.md` 为范围基线、以 `02-mvp-implementation-plan.md` 为架构参考，将原方案推荐的 NestJS + Prisma + BullMQ 全 TypeScript 栈调整为 **Python 后端 + Next.js 前端**。

## 1. 与原方案的对应关系

| 原方案（TS） | 本方案（Python） | 说明 |
|---|---|---|
| NestJS | **FastAPI** | 异步原生、SSE 友好、Pydantic 校验 |
| Prisma | **SQLAlchemy 2.0 + Alembic** | Python 生态最成熟的 ORM + 迁移 |
| BullMQ | **Celery** | 成熟的分布式任务队列 |
| TypeScript contracts | `packages/shared`（前端）+ `backend/`（后端内核） | 前后端语言不同，契约各自维护 |
| NestJS 模块 | FastAPI **APIRouter** 路由组 | 10 个领域模块一一对应 |

**保留不变**：整体架构（API + Worker 分离、Outbox 模式、积分冻结/补偿、适配器抽象、pgvector 记忆检索、OAuth + JWT、短期签名 URL）、数据模型、分阶段开发计划、安全合规基线。

## 2. 总体架构

```text
用户 Web (Next.js)        管理后台 (Next.js /admin)
        │                          │
        └──────────┬───────────────┘
                   ▼
        ┌─────────────────────┐
        │  FastAPI 网关 (API)  │  ← 鉴权 / 限流 / SSE 流式
        │  apps/api (uvicorn)  │
        └─────┬───────┬───────┘
              │       │
     ┌────────┘       └────────┐
     ▼                         ▼
 PostgreSQL+pgvector      Redis (队列/缓存/限流)
     │                         │
     │                         ▼
     │                 ┌────────────────┐
     │                 │  Celery Worker  │  ← 图片/视频/审核
     │                 │  apps/worker    │
     │                 └────────┬────────┘
     │                          │
     ▼                          ▼
 对象存储 (S3兼容+CDN)    LLM / 视觉模型 / 支付 适配器
```

## 3. 技术栈

| 层级 | 技术 | 说明 |
|---|---|---|
| 前端 | Next.js 15 · TypeScript · Tailwind CSS | 用户端 + 管理后台（`/admin`） |
| API | FastAPI · Uvicorn · Pydantic v2 | 领域 API、SSE 流式、鉴权 |
| Worker | Celery · Redis | 图片/视频/审核异步队列 |
| 数据库 | PostgreSQL 16 · SQLAlchemy 2.0 · Alembic | 含 pgvector 扩展 |
| 缓存/队列 | Redis | 限流、Celery broker、会话 |
| 对象存储 | S3 兼容（MinIO 本地） | 短期签名 URL |
| 适配器 | LLM / 视觉 / 支付 / 存储 / 安全 | 供应商可替换 |

## 4. 目录结构

```text
apps/
  web/                # Next.js 用户端 + 管理后台
  api/                # FastAPI 主服务
  worker/             # Celery Worker
backend/              # Python 共享内核
  companion_core/     # 上下文组装 / 记忆检索 / 安全编排
  provider_adapters/  # LLM / 视觉 / 支付 / 存储 / 安全 适配器
  db/                 # SQLAlchemy models + Alembic
  shared/             # 配置、数据库连接、安全工具
packages/
  shared/             # 前端共享 TypeScript 类型/枚举
infra/
  docker/             # Dockerfile
  docker-compose.yml  # PostgreSQL + Redis + MinIO + 全栈
docs/                 # 产品方案与实现方案文档
```

## 5. 后端领域模块（10 个 APIRouter）

| 模块 | 职责 |
|---|---|
| auth | 邮箱注册/登录、OAuth（Google/Facebook）、JWT 令牌、年龄确认 |
| character | 角色档案 CRUD、软删除、时间线 |
| conversation | 会话、消息、SSE 流式回复、反馈 |
| memory | 记忆候选/确认/编辑/删除、向量检索 |
| companion | 上下文组装、记忆检索、安全编排（后端内核） |
| asset | 素材上传预签名 URL、签名访问 |
| generation | 视觉任务创建、积分冻结、Outbox、状态查询 |
| billing | 订阅、积分包、Stripe 结账、Webhook、流水 |
| safety | 文本/图片审核、风险事件、危机响应 |
| admin | 运营看板、用户管理、安全事件 |

## 6. 数据模型（15 张表）

User、AuthIdentity、Character、Conversation、Message、Memory（含 pgvector embedding）、Asset、Work、Template、GenerationTask、OutboxEvent、CreditLedger、Order、Subscription、SafetyEvent。

详见 `backend/db/models/`。

## 7. 适配器接口

| 适配器 | 方法 |
|---|---|
| LLM | `complete` / `stream` / `embed` |
| Vision | `submit` / `get_status` / `cancel` / `normalize_result` / `estimate_cost` |
| Payment | `create_checkout` / `create_customer_portal` / `handle_webhook` / `cancel_subscription` / `refund_payment` |
| Storage | `upload` / `download` / `delete` / `presigned_get_url` / `presigned_put_url` |
| Safety | `check_text` / `check_image` / `check_video` |

每类适配器均提供抽象基类 + OpenAI/Stripe/S3 实现 + Dummy 本地实现。

## 8. 关键设计决策

- **记忆不可静默持久化**：候选记忆必须经用户确认后才能被检索注入上下文。
- **Outbox 模式**：积分冻结与任务创建在同一数据库事务中，Outbox 事件由 Worker 可靠投递到 Celery。
- **积分幂等**：冻结/确认/退回均通过 `idempotency_key` 保证不重复。
- **危机响应**：高风险场景切换到安全响应策略，不使用角色语气。
- **支付以 Webhook 为准**：浏览器跳转仅用于展示，不作为到账依据。

## 9. 分阶段开发

- **阶段 A · 陪伴闭环**：邮箱/OAuth 登录、模板化角色创建、文本聊天、会话历史、显式记忆卡片、角色主页。
- **阶段 B · 视觉陪伴**：角色视觉设定、场景/风格模板、图片任务队列、作品时间线、积分冻结与失败补偿。
- **阶段 C · 商业化与视频**：Stripe 支付、订阅权益、视频生成、完整管理后台、监控告警。

## 10. 本地启动

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d
# 访问 http://localhost:3000
```
