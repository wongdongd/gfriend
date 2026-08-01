'use client';

import { useEffect, useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
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
      api
        .get<{ items: SafetyEvent[] }>('/admin/safety-events')
        .then((res) => setSafetyEvents(res.items));
    }
  }, [tab, users.length, safetyEvents.length]);

  if (loading || !user) {
    return (
      <div className="mesh-bg flex min-h-screen items-center justify-center text-foreground/40">
        {t('common.loading')}
      </div>
    );
  }

  const tabs = [
    { key: 'dashboard' as const, label: t('admin.dashboard'), icon: '◈' },
    { key: 'users' as const, label: t('admin.users'), icon: '◉' },
    { key: 'safety' as const, label: t('admin.safety'), icon: '⬡' },
  ];

  const stats = [
    { label: t('admin.totalUsers'), value: dashboard.total_users ?? 0, color: '#a78bfa' },
    { label: t('admin.totalCharacters'), value: dashboard.total_characters ?? 0, color: '#06b6d4' },
    { label: t('admin.totalTasks'), value: dashboard.total_tasks ?? 0, color: '#34d399' },
    { label: t('admin.pendingSafety'), value: dashboard.pending_safety_events ?? 0, color: '#f43f5e' },
  ];

  return (
    <div className="mesh-bg flex min-h-screen">
      {/* 侧边栏 */}
      <aside className="flex w-56 flex-col border-r border-white/[0.06] bg-[#13141a]">
        <div className="border-b border-white/[0.06] p-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-[#7c3aed] to-[#06b6d4] text-xs text-white">
              ✦
            </div>
            <span className="font-display text-sm font-bold text-foreground">{t('nav.brand')}</span>
          </div>
          <p className="m-0 mt-2 font-mono text-[10px] uppercase tracking-[0.1em] text-foreground/30">
            Admin Console
          </p>
        </div>
        <nav className="flex-1 py-2">
          {tabs.map((tb) => (
            <button
              key={tb.key}
              onClick={() => setTab(tb.key)}
              className={`flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm transition ${
                tab === tb.key
                  ? 'border-l-2 border-primary bg-primary/10 text-[#a78bfa]'
                  : 'border-l-2 border-transparent text-foreground/50 hover:bg-white/5 hover:text-foreground'
              }`}
            >
              <span className="text-base">{tb.icon}</span>
              {tb.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="flex-1 overflow-auto p-6">
        {/* 运营总览 */}
        {tab === 'dashboard' && (
          <div>
            <h2 className="font-display m-0 mb-5 text-2xl font-bold text-foreground">
              {t('admin.opsDashboard')}
            </h2>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {stats.map((s) => (
                <div
                  key={s.label}
                  className="rounded-2xl border border-white/[0.07] bg-card p-5"
                >
                  <p className="m-0 text-sm text-foreground/50">{s.label}</p>
                  <p
                    className="font-display m-0 mt-1 text-3xl font-bold"
                    style={{ color: s.color }}
                  >
                    {s.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 用户管理 */}
        {tab === 'users' && (
          <div>
            <h2 className="font-display m-0 mb-5 text-2xl font-bold text-foreground">
              {t('admin.userManagement')}
            </h2>
            <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-card">
              <table className="w-full text-sm">
                <thead className="bg-white/[0.03] text-foreground/60">
                  <tr>
                    <th className="px-4 py-3 text-left">{t('admin.colEmail')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colRole')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colAgeStatus')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colCredits')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colRegistered')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {users.map((u) => (
                    <tr key={u.id} className="transition hover:bg-white/[0.02]">
                      <td className="px-4 py-3 text-foreground">{u.email}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${
                            u.role === 'admin'
                              ? 'bg-primary/15 text-[#a78bfa]'
                              : 'bg-white/5 text-foreground/60'
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-foreground/60">{u.age_status}</td>
                      <td className="px-4 py-3 font-mono text-[#34d399]">{u.credits_balance}</td>
                      <td className="px-4 py-3 font-mono text-xs text-foreground/30">
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
            <h2 className="font-display m-0 mb-5 text-2xl font-bold text-foreground">
              {t('admin.safetyEvents')}
            </h2>
            <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-card">
              <table className="w-full text-sm">
                <thead className="bg-white/[0.03] text-foreground/60">
                  <tr>
                    <th className="px-4 py-3 text-left">{t('admin.colRiskType')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colSeverity')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colDisposition')}</th>
                    <th className="px-4 py-3 text-left">{t('admin.colTime')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {safetyEvents.map((ev) => (
                    <tr key={ev.id} className="transition hover:bg-white/[0.02]">
                      <td className="px-4 py-3 text-foreground">{ev.risk_type}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${
                            ev.severity === 'critical'
                              ? 'bg-red-500/15 text-red-400'
                              : ev.severity === 'high'
                                ? 'bg-amber-500/15 text-amber-400'
                                : 'bg-white/5 text-foreground/60'
                          }`}
                        >
                          {ev.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-foreground/60">{ev.disposition}</td>
                      <td className="px-4 py-3 font-mono text-xs text-foreground/30">
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
