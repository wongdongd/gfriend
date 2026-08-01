/** API 客户端：封装 fetch、认证令牌与统一错误 */

const API_BASE = '/api';

// 免刷新白名单（401 时直接抛错，不尝试刷新）
const NO_REFRESH_PATHS = new Set(['/auth/login', '/auth/register']);

export class ApiError extends Error {
  code: string;
  status: number;
  params: Record<string, unknown>;

  constructor(code: string, message: string, status: number, params: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.params = params;
  }
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function setTokens(access: string, refresh: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function tryRefresh(): Promise<boolean> {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    if (!NO_REFRESH_PATHS.has(path)) {
      const refreshed = await tryRefresh();
      if (refreshed) return request(path, options);
      clearTokens();
      if (typeof window !== 'undefined') window.location.href = '/';
    }
    const data = await res.json().catch(() => ({}));
    throw new ApiError(
      data.code || 'AUTH_INVALID_CREDENTIALS',
      data.message || 'Authentication failed',
      res.status,
      data.params || {},
    );
  }

  if (!res.ok) {
    const data = (await res.json().catch(() => ({}))) || {};
    if (data && data.code) {
      throw new ApiError(data.code, data.message || 'Request failed', res.status, data.params || {});
    }
    if (res.status === 422 && data.detail) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map((d: { msg?: string }) => d?.msg).filter(Boolean)
        : [String(data.detail)];
      throw new ApiError('VALIDATION_ERROR', detail.join('; ') || 'Validation failed', 422, data.detail);
    }
    throw new ApiError('UNKNOWN', data.detail || data.message || `Request failed: ${res.status}`, res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  /** SSE 流式请求（聊天）。
   * 返回 done 事件携带的 data（含 message_id、safety 等），出错时抛 ApiError。
   */
  stream: async (
    path: string,
    body: unknown,
    onToken: (t: string) => void,
  ): Promise<Record<string, unknown>> => {
    let token = getToken();

    const doStream = async (): Promise<Record<string, unknown>> => {
      const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      // 401 时尝试刷新 token 后重试一次
      if (res.status === 401 && !NO_REFRESH_PATHS.has(path)) {
        const refreshed = await tryRefresh();
        if (refreshed) {
          token = getToken();
          return doStream();
        }
        clearTokens();
        if (typeof window !== 'undefined') window.location.href = '/';
        throw new ApiError('AUTH_INVALID_CREDENTIALS', 'Authentication failed', 401);
      }

      if (!res.ok || !res.body) {
        const errData = await res.json().catch(() => ({}));
        throw new ApiError(
          errData.code || 'UNKNOWN',
          errData.message || `Request failed: ${res.status}`,
          res.status,
          errData.params || {},
        );
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let doneData: Record<string, unknown> = {};

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'token') {
              onToken(data.content);
            } else if (data.type === 'done') {
              doneData = data;
            } else if (data.type === 'error') {
              throw new ApiError(
                'STREAM_ERROR',
                data.message || 'Stream error',
                500,
              );
            }
          } catch (e) {
            // JSON 解析失败时，如果已经是 ApiError 则向上抛出
            if (e instanceof ApiError) throw e;
            // 否则跳过这一行，继续处理后续数据
          }
        }
      }
      return doneData;
    };

    return doStream();
  },
};

/** 将错误翻译为用户可读文案（配合 next-intl） */
export function translateError(
  t: (key: string, values?: Record<string, string | number | Date>) => string,
  err: unknown,
): string {
  if (err instanceof ApiError) {
    const key = `errors.${err.code}`;
    const msg = t(key, err.params as Record<string, string | number | Date>);
    return msg && msg !== key ? msg : err.message || t('errors.unknown');
  }
  return err instanceof Error ? err.message : t('errors.unknown');
}
