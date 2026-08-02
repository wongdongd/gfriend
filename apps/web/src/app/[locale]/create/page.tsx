'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api, translateError } from '@/lib/api';
import Navbar from '@/components/Navbar';

const RELATIONSHIPS = [
  { code: 'friend', icon: '◈', color: '#a78bfa' },
  { code: 'lover', icon: '◉', color: '#f43f5e' },
  { code: 'healer', icon: '◌', color: '#34d399' },
  { code: 'study_buddy', icon: '⬡', color: '#06b6d4' },
  { code: 'listener', icon: '★', color: '#818cf8' },
  { code: 'original', icon: '✦', color: '#f59e0b' },
];

const PERSONALITIES = [
  { code: 'gentle', icon: '◈', color: '#34d399' },
  { code: 'energetic', icon: '◉', color: '#f59e0b' },
  { code: 'calm', icon: '⬡', color: '#06b6d4' },
  { code: 'humorous', icon: '◌', color: '#a78bfa' },
  { code: 'quiet_healing', icon: '✦', color: '#818cf8' },
];

const STYLES = [
  { code: 'cinematic', icon: '◈' },
  { code: 'fresh_life', icon: '◉' },
  { code: 'fashion_mag', icon: '⬡' },
  { code: '3d_anime', icon: '◌' },
  { code: 'anime', icon: '✦' },
  { code: 'retro_film', icon: '★' },
  { code: 'ink_wash', icon: '◆' },
];

const STEP_KEYS = ['stepRelationship', 'stepPersonality', 'stepStyle', 'stepIdentity', 'stepPortrait'];

export default function CreatePage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const t = useTranslations();

  const [step, setStep] = useState(0);
  const [relationship, setRelationship] = useState('');
  const [personality, setPersonality] = useState('');
  const [style, setStyle] = useState('');
  const [name, setName] = useState('');
  const [preference, setPreference] = useState('');
  const [creating, setCreating] = useState(false);

  // 生成阶段状态
  const [characterId, setCharacterId] = useState<string | null>(null);
  const [genTaskId, setGenTaskId] = useState<string | null>(null);
  const [genStatus, setGenStatus] = useState<'idle' | 'pending' | 'success' | 'failed'>('idle');
  const [genUrl, setGenUrl] = useState<string | null>(null);
  const [genError, setGenError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  // 卸载时清理轮询
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const canNext = () => {
    if (step === 0) return !!relationship;
    if (step === 1) return !!personality;
    if (step === 2) return !!style;
    return step === 3 && name.trim().length > 0;
  };

  // 创建角色成功后立即发起首张形象图生成
  const startPortrait = async (charId: string) => {
    setGenStatus('pending');
    setGenError(null);
    setGenUrl(null);
    try {
      const res = await api.createGeneration('image', charId, undefined, style || undefined);
      setGenTaskId(res.task_id);
      // 开始轮询
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const task = await api.getGeneration(res.task_id);
          if (task.status === 'success' || task.status === 'SUCCESS') {
            if (pollRef.current) clearInterval(pollRef.current);
            setGenStatus('success');
            setGenUrl(task.url ?? null);
          } else if (task.status === 'failed' || task.status === 'FAILED' || task.status === 'cancelled' || task.status === 'CANCELLED') {
            if (pollRef.current) clearInterval(pollRef.current);
            setGenStatus('failed');
            setGenError(task.error_message || t('create.genFailed'));
          }
        } catch {
          // 单次轮询失败忽略，下次重试
        }
      }, 2000);
    } catch (err) {
      setGenStatus('failed');
      setGenError(translateError(t, err));
    }
  };

  const regenerate = async () => {
    if (!characterId) return;
    setGenTaskId(null);
    await startPortrait(characterId);
  };

  const create = async () => {
    setCreating(true);
    try {
      const created = await api.post<{ id: string }>('/characters', {
        name: name.trim(),
        companion_preference: preference.trim() || null,
        relationship_template_code: relationship,
        personality_template_code: personality,
        visual_style_code: style,
      });
      setCharacterId(created.id);
      setStep(4);
      // 立刻发起首张形象图生成（不阻塞 UI，状态会驱动渲染）
      startPortrait(created.id);
    } catch (err) {
      alert(translateError(t, err));
    } finally {
      setCreating(false);
    }
  };

  const finishToChat = () => {
    router.push('/chat');
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
              {t('create.workshopEyebrow')}
            </p>
            <h1 className="font-display m-0 text-3xl font-bold text-foreground">
              {t('create.createTitle')}
            </h1>
          </div>
          <button
            onClick={() => router.push('/chat')}
            className="rounded-lg border border-white/10 px-4 py-2 text-[13px] text-foreground/40 transition hover:border-primary/30 hover:text-foreground"
          >
            {t('nav.backToDashboard')}
          </button>
        </div>

        {/* 步骤指示器 */}
        <div className="mb-10 flex items-center">
          {STEP_KEYS.map((sk, i) => (
            <div key={sk} className={`flex items-center ${i < STEP_KEYS.length - 1 ? 'flex-1' : ''}`}>
              <button
                onClick={() => i <= step && setStep(i)}
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[13px] font-bold transition ${
                  i < step
                    ? 'bg-primary text-white'
                    : i === step
                      ? 'bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] text-white'
                      : 'border border-white/10 bg-white/5 text-foreground/30'
                } ${i <= step ? 'cursor-pointer' : 'cursor-default'}`}
              >
                {i < step ? '✓' : i + 1}
              </button>
              <span
                className={`mx-2 text-xs font-semibold ${
                  i <= step ? 'text-foreground' : 'text-foreground/30'
                }`}
              >
                {t(`create.${sk}`)}
              </span>
              {i < STEP_KEYS.length - 1 && (
                <div
                  className={`mx-4 h-px flex-1 ${
                    i < step ? 'bg-primary' : 'bg-white/[0.07]'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* 主内容卡 */}
        <div className="rounded-2xl border border-white/[0.07] bg-card p-9">
          {/* 步骤 0：关系 */}
          {step === 0 && (
            <div className="animate-fade-in-up">
              <h2 className="m-0 mb-1.5 text-xl font-semibold text-foreground">
                {t('create.chooseRelationship')}
              </h2>
              <p className="m-0 mb-7 text-[13px] text-foreground/45">
                {t('create.relationshipDesc')}
              </p>
              <div className="grid grid-cols-2 gap-3.5 md:grid-cols-3">
                {RELATIONSHIPS.map((r) => (
                  <button
                    key={r.code}
                    onClick={() => setRelationship(r.code)}
                    className={`flex flex-col items-center gap-2 rounded-xl border p-5 transition ${
                      relationship === r.code
                        ? ''
                        : 'border-white/[0.08] bg-white/[0.03] hover:border-white/15'
                    }`}
                    style={
                      relationship === r.code
                        ? {
                            background: `${r.color}18`,
                            borderColor: `${r.color}60`,
                          }
                        : {}
                    }
                  >
                    <span
                      className="text-3xl"
                      style={{ color: relationship === r.code ? r.color : 'rgba(240,237,232,0.3)' }}
                    >
                      {r.icon}
                    </span>
                    <span className="text-[13px] font-semibold text-foreground">
                      {t(`create.relationships.${r.code}.label`)}
                    </span>
                    <span className="text-center text-xs text-foreground/50">
                      {t(`create.relationships.${r.code}.desc`)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 步骤 1：性格 */}
          {step === 1 && (
            <div className="animate-fade-in-up">
              <h2 className="m-0 mb-1.5 text-xl font-semibold text-foreground">
                {t('create.choosePersonality')}
              </h2>
              <p className="m-0 mb-7 text-[13px] text-foreground/45">
                {t('create.personalityDesc')}
              </p>
              <div className="flex flex-col gap-2.5">
                {PERSONALITIES.map((p) => (
                  <button
                    key={p.code}
                    onClick={() => setPersonality(p.code)}
                    className={`flex items-center gap-3.5 rounded-xl border p-4 text-left transition ${
                      personality === p.code
                        ? ''
                        : 'border-white/[0.08] bg-white/[0.03] hover:border-white/15'
                    }`}
                    style={
                      personality === p.code
                        ? {
                            background: `${p.color}18`,
                            borderColor: `${p.color}50`,
                          }
                        : {}
                    }
                  >
                    <span className="text-2xl" style={{ color: p.color }}>
                      {p.icon}
                    </span>
                    <div>
                      <p className="m-0 font-semibold text-foreground">
                        {t(`create.personalities.${p.code}.label`)}
                      </p>
                      <p className="m-0 mt-0.5 text-sm text-foreground/50">
                        {t(`create.personalities.${p.code}.desc`)}
                      </p>
                    </div>
                    {personality === p.code && (
                      <span className="ml-auto text-xl text-[#a78bfa]">✓</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 步骤 2：风格 */}
          {step === 2 && (
            <div className="animate-fade-in-up">
              <h2 className="m-0 mb-1.5 text-xl font-semibold text-foreground">
                {t('create.chooseStyle')}
              </h2>
              <p className="m-0 mb-7 text-[13px] text-foreground/45">{t('create.styleDesc')}</p>
              <div className="grid grid-cols-2 gap-3.5 md:grid-cols-3">
                {STYLES.map((s) => (
                  <button
                    key={s.code}
                    onClick={() => setStyle(s.code)}
                    className={`rounded-xl border p-4 text-center transition ${
                      style === s.code
                        ? 'border-primary/50 bg-primary/[0.12]'
                        : 'border-white/[0.08] bg-white/[0.03] hover:border-white/15'
                    }`}
                  >
                    <div className="mb-1 text-2xl text-[#a78bfa]">{s.icon}</div>
                    <div className="text-sm font-medium text-foreground">
                      {t(`create.styles.${s.code}.label`)}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 步骤 3：身份 */}
          {step === 3 && (
            <div className="animate-fade-in-up">
              <h2 className="m-0 mb-1.5 text-xl font-semibold text-foreground">
                {t('create.nameTitle')}
              </h2>
              <p className="m-0 mb-7 text-[13px] text-foreground/45">{t('create.nameDesc')}</p>
              <div className="flex flex-col gap-5">
                <div>
                  <label className="mb-2 block font-mono text-xs tracking-[0.08em] text-foreground/50">
                    {t('create.nameLabel').toUpperCase()}
                  </label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={64}
                    placeholder={t('create.namePlaceholder')}
                    className="w-full rounded-lg border border-white/10 bg-[#1a1b22] px-4 py-2.5 text-[15px] text-foreground outline-none transition focus:border-primary/60"
                  />
                </div>
                <div>
                  <label className="mb-2 block font-mono text-xs tracking-[0.08em] text-foreground/50">
                    {t('create.preferenceLabel').toUpperCase()}{' '}
                    <span className="text-foreground/30">{t('create.preferenceOptional')}</span>
                  </label>
                  <textarea
                    value={preference}
                    onChange={(e) => setPreference(e.target.value)}
                    rows={3}
                    placeholder={t('create.preferencePlaceholder')}
                    className="w-full resize-none rounded-lg border border-white/10 bg-[#1a1b22] px-4 py-2.5 text-sm text-foreground outline-none transition focus:border-primary/60"
                  />
                </div>
              </div>
            </div>
          )}

          {/* 步骤 4：生成首张形象图 */}
          {step === 4 && (
            <div className="animate-fade-in-up">
              <h2 className="m-0 mb-1.5 text-xl font-semibold text-foreground">
                {t('create.portraitTitle')}
              </h2>
              <p className="m-0 mb-2 text-[13px] text-foreground/45">{t('create.portraitDesc')}</p>
              <p className="m-0 mb-7 inline-flex items-center gap-1.5 rounded-md border border-[#34d399]/30 bg-[#34d399]/10 px-2.5 py-1 text-[11px] font-medium text-[#34d399]">
                ✦ {t('create.firstPortraitFreeHint')}
              </p>

              <div className="relative flex min-h-[320px] items-center justify-center overflow-hidden rounded-xl border border-white/[0.07] bg-[#13141b]">
                {/* 生成中：脉冲骨架 */}
                {genStatus === 'pending' && (
                  <div className="flex flex-col items-center gap-4">
                    <div className="h-44 w-44 animate-pulse rounded-full bg-gradient-to-br from-[#7c3aed]/30 to-[#5b21b6]/20" />
                    <div className="flex items-center gap-2 text-[13px] text-foreground/50">
                      <span className="spin inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white" />
                      {t('create.genPending')}
                    </div>
                  </div>
                )}

                {/* 成功：展示图片 */}
                {genStatus === 'success' && genUrl && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={genUrl}
                    alt={name}
                    className="max-h-[420px] w-full object-contain"
                  />
                )}

                {/* 成功但 URL 为空 */}
                {genStatus === 'success' && !genUrl && (
                  <div className="text-[13px] text-foreground/50">{t('create.genNoUrl')}</div>
                )}

                {/* 失败 */}
                {genStatus === 'failed' && (
                  <div className="flex flex-col items-center gap-3 text-center">
                    <div className="text-3xl text-[#f43f5e]">⚠</div>
                    <div className="max-w-md text-[13px] text-foreground/60">
                      {genError || t('create.genFailed')}
                    </div>
                  </div>
                )}
              </div>

              {/* 生成后操作行 */}
              {(genStatus === 'success' || genStatus === 'failed') && (
                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <button
                    onClick={regenerate}
                    disabled={!characterId}
                    className="rounded-lg border border-white/10 px-4 py-2 text-[13px] text-foreground/70 transition hover:border-primary/30 hover:text-foreground disabled:opacity-40"
                  >
                    {t('create.regenerate')}
                  </button>
                  {genStatus === 'success' && (
                    <span className="text-xs text-foreground/40">{t('create.genSuccessHint')}</span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 底部导航按钮 */}
        <div className="mt-6 flex items-center justify-between">
          {step === 4 ? (
            <button
              onClick={() => router.push('/chat')}
              className="rounded-lg border border-white/10 px-5 py-2.5 text-[13px] text-foreground/50 transition hover:border-primary/30 hover:text-foreground"
            >
              {t('create.skip')}
            </button>
          ) : (
            <button
              onClick={() => (step > 0 ? setStep(step - 1) : router.push('/chat'))}
              className="rounded-lg border border-white/10 px-5 py-2.5 text-[13px] text-foreground/50 transition hover:border-primary/30 hover:text-foreground"
            >
              {step === 0 ? t('create.cancel') : t('create.back')}
            </button>
          )}

          {step < 3 ? (
            <button
              onClick={() => canNext() && setStep(step + 1)}
              disabled={!canNext()}
              className="rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-6 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {t('create.continue')}
            </button>
          ) : step === 3 ? (
            <button
              onClick={create}
              disabled={!canNext() || creating}
              className="flex items-center gap-2 rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-6 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
            >
              {creating ? (
                <>
                  <span className="spin inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white" />
                  {t('create.creating')}
                </>
              ) : (
                t('create.createButton')
              )}
            </button>
          ) : (
            // step === 4：生成成功/失败后均可"开始对话"
            <button
              onClick={finishToChat}
              disabled={genStatus === 'pending'}
              className="flex items-center gap-2 rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-6 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {genStatus === 'pending' ? t('create.genPending') : t('create.startChat')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
