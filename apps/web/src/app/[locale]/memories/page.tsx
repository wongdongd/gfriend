'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';

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
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        {t('common.loading')}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">{t('memories.title')}</h1>
          <button onClick={() => router.push('/chat')} className="text-sm text-brand-600 hover:text-brand-700">
            {t('memories.backToChat')}
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 过滤器 */}
        <div className="flex gap-2 mb-6">
          {FILTERS.map((f) => (
            <button
              key={f.v}
              onClick={() => setFilter(f.v)}
              className={`px-3 py-1 rounded-full text-sm ${
                filter === f.v
                  ? 'bg-brand-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-600'
              }`}
            >
              {t(f.lk)}
            </button>
          ))}
        </div>

        {items.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p>{t('memories.empty')}</p>
            <p className="text-sm mt-1">{t('memories.emptyDesc')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((m) => (
              <div key={m.id} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
                <p className="text-gray-900">{m.content}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      m.status === 'confirmed'
                        ? 'bg-green-100 text-green-700'
                        : m.status === 'candidate'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-500'
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
                          className="text-xs text-green-600 hover:text-green-700"
                        >
                          {t('memories.confirm')}
                        </button>
                        <button
                          onClick={() => act(m.id, 'rejected')}
                          className="text-xs text-gray-400 hover:text-gray-600"
                        >
                          {t('memories.reject')}
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => act(m.id, 'delete')}
                      className="text-xs text-red-400 hover:text-red-600"
                    >
                      {t('memories.delete')}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <p className="mt-8 text-center text-xs text-gray-400">{t('memories.footer')}</p>
      </div>
    </div>
  );
}
