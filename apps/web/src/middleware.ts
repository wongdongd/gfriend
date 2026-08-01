import createIntlMiddleware from 'next-intl/middleware';
import { NextResponse, type NextRequest } from 'next/server';
import { routing } from './i18n/routing';

// next-intl 的国际化 middleware
const intlMiddleware = createIntlMiddleware(routing);

/**
 * 统一 middleware：
 * 1. /api/* 请求 → 运行时代理到后端 API（读 process.env.API_URL，无需重新 build）
 * 2. 其它请求 → 交给 next-intl 处理国际化路由
 *
 * 注意：Next.js 的 next.config.js rewrites 在 build 时固化结果，
 * 运行时改环境变量无效。改用 middleware 才能运行时动态读 API_URL。
 */
export default function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // API 代理：把 /api/* 转发到后端
  if (pathname.startsWith('/api/')) {
    const apiBase =
      process.env.API_URL ||
      process.env.RAILWAY_INTERNAL_URL ||
      'http://localhost:8000';
    const target = new URL(pathname + req.nextUrl.search, apiBase);

    // 直接 fetch 后端并返回响应（运行时代理）
    return fetch(target, {
      method: req.method,
      headers: {
        'Content-Type': req.headers.get('Content-Type') || 'application/json',
        ...(req.headers.get('Authorization')
          ? { Authorization: req.headers.get('Authorization')! }
          : {}),
      },
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : req.body,
      // @ts-expect-error Next.js 需要 duplex 才能流式传 body
      duplex: 'half',
    });
  }

  // 非 API 请求交给 next-intl
  return intlMiddleware(req);
}

export const config = {
  // 匹配 API 路径和所有页面路径，排除静态资源
  matcher: ['/((?!_next|_vercel|.*\\..*).*)'],
};
