'use client';

import { Suspense, useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { translateError } from '@/lib/api';
import LanguageSwitcher from '@/components/language-switcher';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login, register } = useAuth();
  const t = useTranslations();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (searchParams.get('mode') === 'register') setMode('register');
  }, [searchParams]);

  useEffect(() => {
    if (user) router.push('/chat');
  }, [user, router]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setProcessing(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err) {
      setError(translateError(t, err));
    } finally {
      setProcessing(false);
    }
  };

  const inputClass = (hasError: boolean) =>
    `w-full rounded-lg border bg-[#1a1b22] px-4 py-3 text-[15px] text-foreground outline-none transition focus:border-primary/60 ${
      hasError ? 'border-red-500/50' : 'border-white/10'
    }`;

  return (
    <div className="mesh-bg flex min-h-screen items-center justify-center px-4 py-24">
      {/* 右上角语言切换 */}
      <div className="absolute right-4 top-4">
        <LanguageSwitcher />
      </div>

      <div className="w-full max-w-[440px] rounded-[20px] border border-white/[0.08] bg-card p-10 shadow-glow-lg">
        {/* 头部 */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-[52px] w-[52px] items-center justify-center rounded-[14px] bg-gradient-to-br from-[#7c3aed] to-[#06b6d4] text-2xl">
            ✦
          </div>
          <h1 className="font-display m-0 mb-1.5 text-2xl font-bold text-foreground">
            {mode === 'login' ? t('login.welcomeBack') : t('login.createAccount')}
          </h1>
          <p className="m-0 text-sm text-foreground/45">
            {mode === 'login' ? t('login.loginSubtitle') : t('login.registerSubtitle')}
          </p>
        </div>

        {/* OAuth 占位按钮 */}
        <div className="mb-6 grid grid-cols-2 gap-3">
          {[
            { icon: 'G', label: 'Google', color: '#ea4335' },
            { icon: 'D', label: 'Discord', color: '#5865f2' },
          ].map((p) => (
            <button
              key={p.label}
              type="button"
              className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] py-2.5 text-[13px] text-foreground transition hover:bg-white/[0.08]"
            >
              <span className="text-[15px] font-bold" style={{ color: p.color }}>
                {p.icon}
              </span>
              {t('login.continueWith', { provider: p.label })}
            </button>
          ))}
        </div>

        {/* 分隔线 */}
          <div className="mb-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-white/[0.07]" />
            <span className="font-mono text-xs text-foreground/30">{t('login.orDivider')}</span>
            <div className="h-px flex-1 bg-white/[0.07]" />
          </div>

        {/* 表单 */}
        <form onSubmit={submit} className="flex flex-col gap-4">
          <div>
            <label className="mb-1.5 block font-mono text-xs tracking-[0.08em] text-foreground/50">
              {t('login.emailLabel')}
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass(!!error)}
              placeholder={t('login.emailPlaceholder')}
            />
          </div>

          <div>
            <label className="mb-1.5 block font-mono text-xs tracking-[0.08em] text-foreground/50">
              {t('login.passwordLabel')}
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass(!!error)}
              placeholder={t('login.passwordHint')}
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={processing}
            className="mt-1 flex items-center justify-center gap-2 rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] py-3 text-[15px] font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {processing ? (
              <>
                <span className="spin inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white" />
                {t('login.authenticating')}
              </>
            ) : mode === 'login' ? (
              t('login.submitLogin')
            ) : (
              t('login.submitRegister')
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-[13px] text-foreground/40">
          {mode === 'login' ? t('login.noAccount') : t('login.haveAccount')}
          <button
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login');
              setError('');
            }}
            className="bg-transparent font-semibold text-[#a78bfa] transition hover:text-[#c4b5fd]"
          >
            {mode === 'login' ? t('login.toggleRegister') : t('login.toggleLogin')}
          </button>
        </p>

        {mode === 'register' && (
          <p className="mt-3 text-center text-[11px] leading-relaxed text-foreground/25">
            {t('login.termsNotice')}
          </p>
        )}
      </div>
    </div>
  );
}

export default function LoginPage() {
  const t = useTranslations();
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-foreground/40">
          {t('common.loading')}
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
