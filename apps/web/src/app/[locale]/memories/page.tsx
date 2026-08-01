'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';

interface Memory {
  id: string;
  content: string;
  status: string;
  created_at?: string;
}

const FILTERS = [
  { v: '', lk: 'memories.filterAll' },
  { v: 'candidate', lk: 'memories.filterCandidate' },
  { v: 'confirmed', lk: 'memories.filterConfirmed' },
];

export default function MemoriesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const t = useTranslations();

  const [items, setItems] = useState<Memory[]>([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (user) load();
  }, [user, filter]);

  const load = async () => {
    const qs = filter ? `?status=${filter}` : '';
    const res = await api.get<{ items: Memory[] }>(`/memories${qs}`);
    setItems(res.items);
  };

  const act = async (id: string, action: string) => {
    if (action === 'delete') {
      await api.delete(`/memories/${id}`);
    } else {
      await api.patch(`/memories/${id}`, { status: action });
    }
    load();
  };

  if (loading) {
    return (
      <div className="mesh-bg flex min-h-screen items-center justify-center text-foreground/40">
        {t('common.loading')}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="mx-auto max-w-4xl px-6 pb-16 pt-32">
        <div className="mb-7 flex items-center justify-between">
          <div>
            <p className="m-0 mb-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-accent">
              Character Memory
            </p>
            <h1 className="font-display m-0 text-3xl font-bold text-foreground">
              {t('memories.title')}
            </h1>
          </div>
          <button
            onClick={() => router.push('/chat')}
            className="rounded-lg border border-white/10 px-4 py-2 text-[13px] text-foreground/40 transition hover:border-primary/30 hover:text-foreground"
          >
            ← Back to Chat
          </button>
        </div>

        {/* 过滤器 */}
        <div className="mb-6 flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.v}
              onClick={() => setFilter(f.v)}
              className={`rounded-full px-3.5 py-1.5 text-sm transition ${
                filter === f.v
                  ? 'bg-primary text-white'
                  : 'border border-white/10 bg-white/5 text-foreground/60 hover:border-primary/30 hover:text-foreground'
              }`}
            >
              {t(f.lk)}
            </button>
          ))}
        </div>

        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.02] py-16 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#a78bfa"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 2v6m0 8v6M2 12h6m8 0h6" />
              </svg>
            </div>
            <p className="mt-3 text-foreground/50">{t('memories.empty')}</p>
            <p className="mt-1 text-sm text-foreground/30">{t('memories.emptyDesc')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((m) => (
              <div
                key={m.id}
                className="card-hover rounded-xl border border-white/[0.07] bg-card p-4"
              >
                <p className="text-sm leading-relaxed text-foreground/80">{m.content}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs ${
                      m.status === 'confirmed'
                        ? 'bg-[#34d399]/15 text-[#34d399]'
                        : m.status === 'candidate'
                          ? 'bg-amber-500/15 text-amber-400'
                          : 'bg-white/5 text-foreground/40'
                    }`}
                  >
                    {m.status === 'confirmed'
                      ? t('memories.statusConfirmed')
                      : m.status === 'candidate'
                        ? t('memories.statusCandidate')
                        : m.status}
                  </span>
                  <div className="flex gap-2">
                    {m.status === 'candidate' && (
                      <>
                        <button
                          onClick={() => act(m.id, 'confirmed')}
                          className="text-xs text-[#34d399] transition hover:text-[#6ee7b7]"
                        >
                          {t('memories.confirm')}
                        </button>
                        <button
                          onClick={() => act(m.id, 'rejected')}
                          className="text-xs text-foreground/40 transition hover:text-foreground/60"
                        >
                          {t('memories.reject')}
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => act(m.id, 'delete')}
                      className="text-xs text-red-400 transition hover:text-red-300"
                    >
                      {t('memories.delete')}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <p className="mt-8 text-center text-xs text-foreground/30">{t('memories.footer')}</p>
      </div>
    </div>
  );
}
