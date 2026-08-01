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
export default async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // API 代理：把 /api/* 转发到后端
  if (pathname.startsWith('/api/')) {
    const apiBase =
      process.env.API_URL ||
      process.env.RAILWAY_INTERNAL_URL ||
      'http://localhost:8000';
    const target = new URL(pathname + req.nextUrl.search, apiBase);

    // 调试日志：打印实际转发的后端地址（方便排查连接问题）
    console.log(`[api-proxy] ${req.method} ${pathname} → ${target.href}`);

    // 转发必要的请求头，包括 Accept-Language（后端多语言危机响应依赖它）
    const forwardHeaders = new Headers();
    const passthrough = [
      'content-type',
      'authorization',
      'accept-language',
      'accept',
      'user-agent',
    ];
    for (const key of passthrough) {
      const val = req.headers.get(key);
      if (val) forwardHeaders.set(key, val);
    }

    // 读取请求体（GET/HEAD 无 body）
    let body: BodyInit | undefined = undefined;
    if (!['GET', 'HEAD'].includes(req.method)) {
      try {
        body = await req.text();
      } catch {
        // 读取 body 失败时传 undefined
      }
    }

    // 直接 fetch 后端并返回响应（运行时代理）
    try {
      const upstream = await fetch(target, {
        method: req.method,
        headers: forwardHeaders,
        body,
      });
      // 透传后端响应（状态码、头、体）
      const respHeaders = new Headers();
      upstream.headers.forEach((v, k) => {
        // 跳过 transfer-encoding，避免 Next.js 重复压缩
        if (k.toLowerCase() !== 'transfer-encoding') respHeaders.set(k, v);
      });
      const respBody = await upstream.text();
      console.log(
        `[api-proxy] ← ${upstream.status} ${upstream.statusText} (${respBody.length} bytes)`,
      );
      return new NextResponse(respBody, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: respHeaders,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error(`[api-proxy] fetch failed: ${msg}`);
      return NextResponse.json(
        {
          error: 'BAD_GATEWAY',
          message: `API proxy error: ${msg}`,
          detail: `Could not reach backend at ${target.origin}`,
        },
        { status: 502 },
      );
    }
  }

  // 非 API 请求交给 next-intl
  return intlMiddleware(req);
}

export const config = {
  // 匹配 API 路径和所有页面路径，排除静态资源
  matcher: ['/((?!_next|_vercel|.*\\..*).*)'],
};
