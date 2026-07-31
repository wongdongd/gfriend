'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';

interface Dashboard {
  total_users?: number;
  total_characters?: number;
  total_tasks?: number;
  pending_safety_events?: number;
}

interface UserRow {
  id: string;
  email: string;
  role: string;
  age_status: string;
  credits_balance: number;
  created_at: string;
}

interface SafetyEvent {
  id: string;
  risk_type: string;
  severity: string;
  disposition: string;
  created_at: string;
}

const LOCALE_MAP: Record<string, string> = { en: 'en-US', zh: 'zh-CN', ja: 'ja-JP', es: 'es-ES' };

export default function AdminPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const t = useTranslations();
  const locale = useLocale();
  const dateLocale = LOCALE_MAP[locale] || 'en-US';

  const [dashboard, setDashboard] = useState<Dashboard>({});
  const [tab, setTab] = useState<'dashboard' | 'users' | 'safety'>('dashboard');
  const [users, setUsers] = useState<UserRow[]>([]);
  const [safetyEvents, setSafetyEvents] = useState<SafetyEvent[]>([]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push('/login');
    } else if (user.role !== 'admin' && user.role !== 'operator') {
      router.push('/chat');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user && (user.role === 'admin' || user.role === 'operator')) {
      api.get<Dashboard>('/admin/dashboard').then(setDashboard);
    }
  }, [user]);

  useEffect(() => {
    if (tab === 'users' && users.length === 0) {
      api.get<{ items: UserRow[] }>('/admin/users').then((res) => setUsers(res.items));
    }
    if (tab === 'safety' && safetyEvents.length === 0) {
      api.get<{ items: SafetyEvent[] }>('/admin/safety-events').then((res) => setSafetyEvents(res.items));
    }
  }, [tab, users.length, safetyEvents.length]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        {t('common.loading')}
      </div>
    );
  }

  const tabs = [
    { key: 'dashboard' as const, label: t('admin.dashboard'), icon: '📊' },
    { key: 'users' as const, label: t('admin.users'), icon: '👥' },
    { key: 'safety' as const, label: t('admin.safety'), icon: '🛡️' },
  ];

  const stats = [
    { label: t('admin.totalUsers'), value: dashboard.total_users ?? 0 },
    { label: t('admin.totalCharacters'), value: dashboard.total_characters ?? 0 },
    { label: t('admin.totalTasks'), value: dashboard.total_tasks ?? 0 },
    { label: t('admin.pendingSafety'), value: dashboard.pending_safety_events ?? 0 },
  ];

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* 侧边栏 */}
      <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="font-bold text-white">{t('admin.title')}</h1>
        </div>
        <nav className="flex-1 py-2">
          {tabs.map((tb) => (
            <button
              key={tb.key}
              onClick={() => setTab(tb.key)}
              className={`w-full text-left px-4 py-2.5 text-sm hover:bg-gray-800 ${
                tab === tb.key ? 'bg-gray-800 text-white border-l-2 border-brand-500' : ''
              }`}
            >
              <span className="mr-2">{tb.icon}</span>
              {tb.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="flex-1 p-6 overflow-auto">
        {/* 运营总览 */}
        {tab === 'dashboard' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">{t('admin.opsDashboard')}</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {stats.map((s) => (
                <div key={s.label} className="bg-white rounded-xl p-5 shadow-sm">
                  <p className="text-sm text-gray-500">{s.label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{s.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 用户管理 */}
        {tab === 'users' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">{t('admin.userManagement')}</h2>
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="px-4 py-3 text-left">{t('admin.colEmail')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colRole')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colAgeStatus')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colCredits')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colRegistered')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">{u.email}</td>
                      <td className="px-4 py-3">{u.role}</td>
                      <td className="px-4 py-3">{u.age_status}</td>
                      <td className="px-4 py-3">{u.credits_balance}</td>
                      <td className="px-4 py-3 text-gray-400">
                        {new Date(u.created_at).toLocaleDateString(dateLocale)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 安全事件 */}
        {tab === 'safety' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">{t('admin.safetyEvents')}</h2>
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="px-4 py-3 text-left">{t('admin.colRiskType')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colSeverity')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colDisposition')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colTime')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {safetyEvents.map((ev) => (
                    <tr key={ev.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">{ev.risk_type}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs ${
                            ev.severity === 'critical'
                              ? 'bg-red-100 text-red-700'
                              : ev.severity === 'high'
                                ? 'bg-orange-100 text-orange-700'
                                : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {ev.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3">{ev.disposition}</td>
                      <td className="px-4 py-3 text-gray-400">
                        {new Date(ev.created_at).toLocaleString(dateLocale)}
                      </td>
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
