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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="flex justify-end mb-2">
          <LanguageSwitcher />
        </div>

        <div className="text-center mb-8">
          <span className="text-4xl">🤝</span>
          <h1 className="mt-4 text-2xl font-bold text-gray-900">
            {mode === 'login' ? t('login.welcomeBack') : t('login.createAccount')}
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            {mode === 'login' ? t('login.loginSubtitle') : t('login.registerSubtitle')}
          </p>
        </div>

        <form
          onSubmit={submit}
          className="space-y-4 bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('login.email')}</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
              placeholder={t('login.emailPlaceholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('login.password')}
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
              placeholder={t('login.passwordPlaceholder')}
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={processing}
            className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition"
          >
            {processing
              ? t('login.processing')
              : mode === 'login'
                ? t('login.submitLogin')
                : t('login.submitRegister')}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          {mode === 'login' ? t('login.noAccount') : t('login.haveAccount')}
          <button
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="ml-1 text-brand-600 hover:text-brand-700 font-medium"
          >
            {mode === 'login' ? t('login.toggleRegister') : t('login.toggleLogin')}
          </button>
        </p>

        <p className="mt-6 text-center text-xs text-gray-400">{t('login.aiNotice')}</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  const t = useTranslations();
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-gray-400">
          {t('common.loading')}
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
