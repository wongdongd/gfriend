# 前端 Dockerfile（Next.js 15 生产构建）
# Railway 构建：Root Directory = /, Dockerfile path = infra/docker/web.Dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
RUN npm install -g pnpm@10
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/
COPY packages/shared/package.json ./packages/shared/
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
WORKDIR /app
RUN npm install -g pnpm@10
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# 构建时注入 API URL（Railway 会在运行时通过环境变量注入）
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
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
# pnpm workspace：apps/web/node_modules 是指向根 .pnpm 的符号链接目录，必须一并复制，否则 next 找不到
COPY --from=builder /app/apps/web/node_modules ./apps/web/node_modules
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
# 使用 shell 形式以正确展开 Railway 注入的 PORT 环境变量
CMD ["sh", "-c", "pnpm --filter @companion/web start --port ${PORT:-3000}"]
