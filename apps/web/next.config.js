const createNextIntlPlugin = require('next-intl/plugin');

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  // API 代理已移至 src/middleware.ts（运行时动态读 API_URL，无需重新 build）
};

module.exports = withNextIntl(nextConfig);
