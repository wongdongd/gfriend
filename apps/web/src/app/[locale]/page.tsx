'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import LanguageSwitcher from '@/components/language-switcher';

const VALUE_PROPS = [
  { icon: '✨', titleKey: 'home.valueExclusiveTitle', descKey: 'home.valueExclusiveDesc' },
  { icon: '💬', titleKey: 'home.valueCompanionshipTitle', descKey: 'home.valueCompanionshipDesc' },
  { icon: '📸', titleKey: 'home.valueVisibleTitle', descKey: 'home.valueVisibleDesc' },
  { icon: '🌱', titleKey: 'home.valueGrowthTitle', descKey: 'home.valueGrowthDesc' },
];

export default function HomePage() {
  const { user, loading } = useAuth();
  const t = useTranslations();

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 via-white to-white">
      {/* 导航栏 */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🤝</span>
          <span className="text-xl font-bold text-brand-700">{t('nav.brand')}</span>
        </div>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          {loading ? null : user ? (
            <>
              <Link href="/chat" className="text-gray-600 hover:text-brand-700">
                {t('nav.myCharacters')}
              </Link>
              <Link
                href="/create"
                className="rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                {t('nav.create')}
              </Link>
            </>
          ) : (
            <>
              <Link href="/login" className="text-gray-600 hover:text-brand-700">
                {t('nav.login')}
              </Link>
              <Link
                href="/login?mode=register"
                className="rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                {t('nav.getStarted')}
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <h1 className="text-5xl font-bold tracking-tight text-gray-900">
          {t('home.heroTitle1')}
          <span className="text-brand-600"> {t('home.heroTitle2')}</span>
        </h1>
        <p className="mt-6 text-lg text-gray-600 leading-relaxed">{t('home.heroSubtitle')}</p>
        <div className="mt-10 flex justify-center gap-4">
          <Link
            href={user ? '/create' : '/login?mode=register'}
            className="rounded-full bg-brand-600 px-8 py-3 text-base font-medium text-white shadow-lg hover:bg-brand-700 transition"
          >
            {user ? t('nav.create') : t('nav.freeStart')}
          </Link>
          {user && (
            <Link
              href="/chat"
              className="rounded-full border border-gray-300 px-8 py-3 text-base font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              {t('nav.continueChat')}
            </Link>
          )}
        </div>
      </section>

      {/* 价值主张 */}
      <section className="max-w-5xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {VALUE_PROPS.map((v) => (
          <div key={v.titleKey} className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="text-3xl mb-3">{v.icon}</div>
            <h3 className="font-semibold text-gray-900">{t(v.titleKey)}</h3>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">{t(v.descKey)}</p>
          </div>
        ))}
      </section>

      {/* 安全透明 */}
      <section className="max-w-3xl mx-auto px-6 py-12 text-center">
        <div className="rounded-2xl bg-gray-50 p-8">
          <h2 className="text-lg font-semibold text-gray-900">{t('home.safetyTitle')}</h2>
          <p className="mt-3 text-sm text-gray-600 leading-relaxed">{t('home.safetyDesc')}</p>
        </div>
      </section>

      <footer className="text-center py-8 text-sm text-gray-400">{t('home.footer')}</footer>
    </div>
  );
}
