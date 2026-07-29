'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';

export default function AdminPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<Record<string, number>>({});
  const [tab, setTab] = useState<'dashboard' | 'users' | 'safety'>('dashboard');
  const [users, setUsers] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    if (!loading) {
      if (!user) router.push('/login');
      else if (user.role !== 'admin' && user.role !== 'operator') router.push('/chat');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user && (user.role === 'admin' || user.role === 'operator')) {
      api.get<Record<string, number>>('/admin/dashboard').then(setStats);
    }
  }, [user]);

  useEffect(() => {
    if (tab === 'users' && users.length === 0) {
      api.get<{ items: any[] }>('/admin/users').then((res) => setUsers(res.items));
    }
    if (tab === 'safety' && events.length === 0) {
      api.get<{ items: any[] }>('/admin/safety-events').then((res) => setEvents(res.items));
    }
  }, [tab]);

  if (loading || !user) return <div className="min-h-screen flex items-center justify-center text-gray-400">加载中...</div>;

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* 侧边栏 */}
      <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="font-bold text-white">管理后台</h1>
        </div>
        <nav className="flex-1 py-2">
          {[
            { key: 'dashboard', label: '看板', icon: '📊' },
            { key: 'users', label: '用户', icon: '👥' },
            { key: 'safety', label: '安全', icon: '🛡️' },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key as any)}
              className={`w-full text-left px-4 py-2.5 text-sm hover:bg-gray-800 ${
                tab === t.key ? 'bg-gray-800 text-white border-l-2 border-brand-500' : ''
              }`}
            >
              <span className="mr-2">{t.icon}</span>
              {t.label}
            </button>
          ))}
        </nav>
      </aside>

      {/* 主区域 */}
      <main className="flex-1 p-6 overflow-auto">
        {tab === 'dashboard' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">运营看板</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: '用户总数', value: stats.total_users ?? 0 },
                { label: '角色总数', value: stats.total_characters ?? 0 },
                { label: '任务总数', value: stats.total_tasks ?? 0 },
                { label: '待处理安全事件', value: stats.pending_safety_events ?? 0 },
              ].map((s) => (
                <div key={s.label} className="bg-white rounded-xl p-5 shadow-sm">
                  <p className="text-sm text-gray-500">{s.label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{s.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'users' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">用户管理</h2>
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="px-4 py-3 text-left">邮箱</th>
                    <th className="px-4 py-3 text-left">角色</th>
                    <th className="px-4 py-3 text-left">年龄状态</th>
                    <th className="px-4 py-3 text-left">积分</th>
                    <th className="px-4 py-3 text-left">注册时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">{u.email}</td>
                      <td className="px-4 py-3">{u.role}</td>
                      <td className="px-4 py-3">{u.age_status}</td>
                      <td className="px-4 py-3">{u.credits_balance}</td>
                      <td className="px-4 py-3 text-gray-400">{new Date(u.created_at).toLocaleDateString('zh-CN')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === 'safety' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">安全事件</h2>
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="px-4 py-3 text-left">风险类型</th>
                    <th className="px-4 py-3 text-left">严重程度</th>
                    <th className="px-4 py-3 text-left">处置状态</th>
                    <th className="px-4 py-3 text-left">时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {events.map((e) => (
                    <tr key={e.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">{e.risk_type}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs ${
                          e.severity === 'critical' ? 'bg-red-100 text-red-700' :
                          e.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>{e.severity}</span>
                      </td>
                      <td className="px-4 py-3">{e.disposition}</td>
                      <td className="px-4 py-3 text-gray-400">{new Date(e.created_at).toLocaleString('zh-CN')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
