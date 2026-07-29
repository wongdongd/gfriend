/** @type {import('next').NextConfig} */
const nextConfig = {
  // 后端 API 代理（开发环境）
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
