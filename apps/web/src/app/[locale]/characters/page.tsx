'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api, translateError } from '@/lib/api';
import Navbar from '@/components/Navbar';
import type { Character } from '@companion/shared';

// 视觉风格 → 卡片渐变配色（与 create 页 STYLES 数组保持一致）
const STYLE_GRADIENTS: Record<string, string> = {
  cinematic: 'from-[#7c3aed]/30 to-[#5b21b6]/20',
  fresh_life: 'from-[#34d399]/30 to-[#06b6d4]/20',
  fashion_mag: 'from-[#f43f5e]/30 to-[#f59e0b]/20',
  '3d_anime': 'from-[#a78bfa]/30 to-[#818cf8]/20',
  anime: 'from-[#06b6d4]/30 to-[#a78bfa]/20',
  retro_film: 'from-[#f59e0b]/30 to-[#f43f5e]/20',
  ink_wash: 'from-[#818cf8]/30 to-[#34d399]/20',
};

const STYLE_DEFAULT = 'from-[#7c3aed]/30 to-[#5b21b6]/20';

export default function CharactersPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const t = useTranslations();

  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading2, setLoading2] = useState(true);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  const load = async () => {
    if (!user) return;
    setLoading2(true);
    try {
      const data = await api.get<Character[]>('/characters');
      setCharacters(Array.isArray(data) ? data : []);
    } catch {
      // 静默失败
    } finally {
      setLoading2(false);
    }
  };

  useEffect(() => {
    if (user) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const startChat = (id: string) => {
    router.push(`/chat?character_id=${id}`);
  };

  const removeCharacter = async (id: string) => {
    setBusyId(id);
    try {
      await api.delete(`/characters/${id}`);
      setCharacters((prev) => prev.filter((c) => c.id !== id));
      setConfirmingId(null);
    } catch (err) {
      alert(translateError(t, err));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="mesh-bg flex min-h-screen items-center justify-center text-foreground/40">
        {t('common.loading')}
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="mx-auto max-w-[1280px] px-6 pb-16 pt-32">
        {/* 头部 */}
        <div className="mb-9 flex items-center justify-between">
          <div>
            <p className="m-0 mb-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-accent">
              {t('nav.myCharacters')}
            </p>
            <h1 className="font-display m-0 text-3xl font-bold text-foreground">
              {t('characters.title')}
            </h1>
          </div>
          <button
            onClick={() => router.push('/create')}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
          >
            <span className="text-base">✦</span>
            {t('characters.createNew')}
          </button>
        </div>

        {/* 加载中 */}
        {loading2 && (
          <div className="flex items-center justify-center py-20 text-foreground/40">
            <span className="spin inline-block h-5 w-5 rounded-full border-2 border-white/30 border-t-white" />
            <span className="ml-3 text-sm">{t('common.loading')}</span>
          </div>
        )}

        {/* 空状态 */}
        {!loading2 && characters.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-primary/15 to-accent/10 shadow-inner">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div className="space-y-1">
              <p className="text-lg font-medium text-foreground/70">{t('characters.empty')}</p>
              <p className="text-sm text-foreground/40">{t('characters.emptyHint')}</p>
            </div>
            <button
              onClick={() => router.push('/create')}
              className="mt-2 rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-6 py-2.5 font-medium text-white shadow-md transition hover:shadow-glow"
            >
              {t('characters.createNew')}
            </button>
          </div>
        )}

        {/* 角色卡片网格 */}
        {!loading2 && characters.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {characters.map((c) => {
              const gradient = STYLE_GRADIENTS[c.visual_style_code ?? ''] ?? STYLE_DEFAULT;
              const initials = (c.name?.[0] ?? '?').toUpperCase();
              return (
                <div
                  key={c.id}
                  className={`group relative overflow-hidden rounded-2xl border border-white/[0.07] bg-card transition hover:border-primary/30 ${confirmingId === c.id ? 'ring-2 ring-red-400/40' : ''}`}
                >
                  {/* 卡片顶部视觉区 */}
                  <div className={`relative flex h-28 items-center justify-center bg-gradient-to-br ${gradient}`}>
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#0a0b0f]/40 text-2xl font-bold text-foreground backdrop-blur-sm">
                      {initials}
                    </div>
                  </div>

                  {/* 卡片信息 */}
                  <div className="p-5">
                    <div className="mb-1 flex items-center gap-2">
                      <h3 className="m-0 truncate text-lg font-semibold text-foreground">{c.name}</h3>
                      <span className="inline-flex h-1.5 w-1.5 shrink-0 rounded-full bg-[#34d399]" title={t('chat.online')} />
                    </div>
                    <p className="m-0 mb-1 truncate text-xs text-foreground/50">
                      {c.relationship_template_code
                        ? t(`create.relationships.${c.relationship_template_code}.label` as never)
                        : t('characters.unknown')}
                    </p>
                    <p className="m-0 mb-4 text-[11px] text-foreground/35">
                      {new Date(c.created_at).toLocaleDateString()}
                    </p>

                    {/* 操作 */}
                    {confirmingId === c.id ? (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setConfirmingId(null)}
                          disabled={busyId === c.id}
                          className="flex-1 rounded-md border border-white/10 px-3 py-1.5 text-xs text-foreground/60 transition hover:border-white/20 disabled:opacity-40"
                        >
                          {t('characters.cancelDelete')}
                        </button>
                        <button
                          onClick={() => removeCharacter(c.id)}
                          disabled={busyId === c.id}
                          className="flex-1 rounded-md bg-red-500/80 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-red-500 disabled:opacity-40"
                        >
                          {busyId === c.id ? t('common.loading') : t('characters.confirmDelete')}
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => startChat(c.id)}
                          className="flex-1 rounded-md bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-3 py-2 text-xs font-semibold text-white transition hover:opacity-90"
                        >
                          {t('characters.startChat')}
                        </button>
                        <button
                          onClick={() => setConfirmingId(c.id)}
                          className="rounded-md border border-white/10 px-3 py-2 text-xs text-foreground/50 transition hover:border-red-400/40 hover:text-red-400"
                          title={t('characters.delete')}
                        >
                          ✕
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
