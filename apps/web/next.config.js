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
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

module.exports = withNextIntl(nextConfig);
