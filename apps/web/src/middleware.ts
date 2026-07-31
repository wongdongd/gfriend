import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // 匹配所有路径，排除静态资源与 API 代理
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
};
