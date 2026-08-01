# 前端 Dockerfile（Next.js 15 生产构建）
# Railway 构建：Root Directory = /, Dockerfile path = infra/docker/web.Dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
RUN npm install -g pnpm@10
# workspace 配置 + lockfile 必须一并复制，否则 pnpm 不识别 monorepo 且 --frozen-lockfile 会失败
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/
COPY packages/shared/package.json ./packages/shared/
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
WORKDIR /app
RUN npm install -g pnpm@10
# pnpm hoisting：依赖主要在根 node_modules，子包 node_modules 多为符号链接，
# 必须连同根 node_modules 一起复制才能保留符号链接结构
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY --from=deps /app/packages/shared/node_modules ./packages/shared/node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# 构建时注入公开 API URL（浏览器端可见）
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# API_URL 在运行时由 middleware 读取，无需 build 时注入
RUN pnpm --filter @companion/web build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# runner 阶段是独立基础镜像，需重新安装 pnpm（全局安装未被 COPY 进 runner）
RUN npm install -g pnpm@10
COPY --from=builder /app/apps/web/.next ./apps/web/.next
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder /app/apps/web/package.json ./apps/web/package.json
COPY --from=builder /app/apps/web/next.config.js ./apps/web/next.config.js
# pnpm workspace：apps/web/node_modules 是指向根 .pnpm 的符号链接目录，必须连同根 node_modules 一并复制
COPY --from=builder /app/apps/web/node_modules ./apps/web/node_modules
COPY --from=builder /app/packages/shared ./packages/shared
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/pnpm-workspace.yaml ./pnpm-workspace.yaml

# 使用 node:22-alpine 内置的 node 用户（UID 1000）运行，避免以 root 运行
RUN chown -R node:node /app
USER node

EXPOSE 3000
# 使用 shell 形式以正确展开 Railway 注入的 PORT 环境变量
CMD ["sh", "-c", "pnpm --filter @companion/web start --port ${PORT:-3000}"]
