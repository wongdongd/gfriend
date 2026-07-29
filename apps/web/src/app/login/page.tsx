'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { user, login, register } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (params.get('mode') === 'register') setMode('register');
  }, [params]);

  useEffect(() => {
    if (user) router.push('/chat');
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-4xl">🤝</span>
          <h1 className="mt-4 text-2xl font-bold text-gray-900">
            {mode === 'login' ? '欢迎回来' : '创建账户'}
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            {mode === 'login' ? '登录继续与你的角色对话' : '开始创建你的专属 AI 陪伴人物'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
              placeholder="至少 6 位"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition"
          >
            {loading ? '处理中...' : mode === 'login' ? '登录' : '注册'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          {mode === 'login' ? '还没有账户？' : '已有账户？'}
          <button
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="ml-1 text-brand-600 hover:text-brand-700 font-medium"
          >
            {mode === 'login' ? '注册' : '登录'}
          </button>
        </p>

        <p className="mt-6 text-center text-xs text-gray-400">
          这是一个 AI 产品，角色不具备真实意识。
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">加载中...</div>}>
      <LoginForm />
    </Suspense>
  );
}
