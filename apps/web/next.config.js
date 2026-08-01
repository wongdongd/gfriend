const createNextIntlPlugin = require('next-intl/plugin');

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  // 后端 API 代理
  // 优先级：API_URL > RAILWAY_INTERNAL_URL(同项目 API 服务内部地址) > 本地默认
  async rewrites() {
    const apiBase =
      process.env.API_URL ||
      process.env.RAILWAY_INTERNAL_URL ||
      'http://localhost:8000';
    // 启动时打印实际使用的 API 地址，便于在 Railway 日志里排查
    console.log(`[rewrites] API_URL=${process.env.API_URL || '(未设置)'}`);
    console.log(`[rewrites] RAILWAY_INTERNAL_URL=${process.env.RAILWAY_INTERNAL_URL || '(未设置)'}`);
    console.log(`[rewrites] 实际代理目标: ${apiBase}/api/*`);
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

module.exports = withNextIntl(nextConfig);
