'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import Navbar from '@/components/Navbar';

const FEATURE_ICONS = [
  { icon: '◈', color: '#7c3aed' },
  { icon: '◉', color: '#06b6d4' },
  { icon: '⬡', color: '#a78bfa' },
  { icon: '◌', color: '#34d399' },
];

const STATS_VALUES = ['128K+', '24/7', '12M+', '99.7%'];

const TESTIMONIAL_META = [
  { name: 'Zara Voss', handle: '@zvoss_creates', tier: 'Studio' },
  { name: 'Kenji Ota', handle: '@kenjibuilds', tier: 'Creator' },
  { name: 'Mira Elaine', handle: '@mira.elaine', tier: 'Studio' },
];

export default function HomePage() {
  const { user, loading } = useAuth();
  const t = useTranslations();

  const features = [1, 2, 3, 4].map((n) => ({
    ...FEATURE_ICONS[n - 1],
    title: t(`home.feature${n}Title`),
    desc: t(`home.feature${n}Desc`),
  }));

  const stats = [
    { value: STATS_VALUES[0], label: t('home.statsCompanions') },
    { value: STATS_VALUES[1], label: t('home.statsOnline') },
    { value: STATS_VALUES[2], label: t('home.statsChats') },
    { value: STATS_VALUES[3], label: t('home.statsUptime') },
  ];

  const testimonials = TESTIMONIAL_META.map((tm, i) => ({
    ...tm,
    text: t(`home.testimonial${i + 1}Text`),
  }));

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero */}
      <section className="mesh-bg relative overflow-hidden px-6 pb-24 pt-36">
        <div className="grid-lines pointer-events-none absolute inset-0" />
        <div className="relative mx-auto grid max-w-[1280px] grid-cols-1 items-center gap-10 lg:grid-cols-2 lg:gap-14">
          {/* 左：文案 */}
          <div className="animate-fade-in-up">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/[0.08] px-3.5 py-1.5 font-mono text-xs uppercase tracking-[0.1em] text-[#a78bfa]">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#a78bfa]" />
              {t('home.betaBadge')}
            </div>

            <h1 className="font-display text-4xl font-black leading-[1.1] tracking-tight text-foreground sm:text-5xl xl:text-6xl">
              {t('home.heroTitle1')}
              <br />
              <span className="shimmer-text">{t('home.heroTitle2')}</span>
            </h1>

            <p className="mt-6 max-w-[480px] text-lg leading-relaxed text-foreground/60">
              {t('home.heroSubtitle')}
            </p>

            <div className="mt-10 flex flex-wrap gap-3.5">
              <Link
                href={user ? '/create' : '/login?mode=register'}
                className="pulse-glow rounded-[10px] bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-8 py-3.5 text-base font-semibold text-white"
              >
                {user ? t('home.heroCtaStart') : t('home.heroCtaFree')}
              </Link>
              <Link
                href="/billing"
                className="rounded-[10px] border border-white/[0.12] bg-white/5 px-8 py-3.5 text-base font-medium text-foreground transition hover:bg-white/10"
              >
                {t('home.viewPlans')}
              </Link>
            </div>

            {/* Trust strip */}
            <div className="mt-12 flex items-center gap-4">
              <div className="flex -space-x-2.5">
                {['A', 'K', 'M', 'Z'].map((c, i) => (
                  <div
                    key={i}
                    className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-background bg-gradient-to-br from-[#7c3aed] to-[#06b6d4] text-xs font-bold text-white"
                  >
                    {c}
                  </div>
                ))}
              </div>
              <p className="text-[13px] text-foreground/50">
                <strong className="text-[#a78bfa]">{t('home.trustCount')}</strong>{' '}
                {t('home.trustText')}
              </p>
            </div>
          </div>

          {/* 右：Hero 视觉占位 */}
          <div className="relative flex justify-center">
            <div className="relative aspect-[4/5] w-full max-w-[460px] overflow-hidden rounded-3xl border border-primary/30 shadow-glow-lg">
              {/* 纯 CSS 渐变占位，不依赖外部图片 */}
              <div className="mesh-bg h-full w-full" />
              <div className="absolute inset-0 bg-gradient-to-t from-background/80 via-transparent to-transparent" />

              {/* 浮动统计卡 */}
              <div className="absolute inset-x-6 bottom-6 flex items-center justify-between rounded-xl border border-primary/20 bg-[#13141a]/90 px-4.5 py-3.5 backdrop-blur-md">
                <div>
                  <p className="m-0 font-mono text-xs text-foreground/40">{t('home.heroCardLabel')}</p>
                  <p className="m-0 mt-0.5 text-[15px] font-semibold text-foreground">{t('home.heroCardName')}</p>
                </div>
                <div className="text-right">
                  <p className="m-0 font-mono text-xs text-[#a78bfa]">{t('home.heroCardStatus')}</p>
                  <p className="m-0 mt-0.5 text-[13px] text-foreground/50">{t('home.heroCardMood')}</p>
                </div>
              </div>
            </div>

            {/* 浮动徽章 */}
            <div className="absolute -right-4 -top-4 rounded-xl border border-accent/40 bg-accent/10 px-4 py-2.5 backdrop-blur-md">
              <p className="m-0 font-mono text-[11px] text-accent">{t('home.heroBadgeLabel')}</p>
              <p className="m-0 mt-0.5 text-sm font-semibold text-foreground">{t('home.heroBadgeValue')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* 统计条 */}
      <section className="border-y border-white/[0.06]">
        <div className="mx-auto grid max-w-[1280px] grid-cols-2 gap-px md:grid-cols-4">
          {stats.map((s, i) => (
            <div
              key={i}
              className="px-6 py-10 text-center [&:not(:last-child)]:border-r [&:not(:last-child)]:border-white/[0.06]"
            >
              <p className="m-0 mb-1 font-display text-4xl font-bold text-[#a78bfa]">{s.value}</p>
              <p className="m-0 font-mono text-[13px] tracking-[0.08em] text-foreground/40">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 特性 */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-[1280px]">
          <div className="mb-14 text-center">
            <p className="mb-3 font-mono text-[11px] uppercase tracking-[0.15em] text-accent">
              {t('home.featuresEyebrow')}
            </p>
            <h2 className="m-0 mb-4 font-display text-3xl font-bold text-foreground sm:text-4xl xl:text-5xl">
              {t('home.featuresTitle')}
            </h2>
            <p className="mx-auto max-w-[480px] text-base text-foreground/50">
              {t('home.featuresSubtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {features.map((f, i) => (
              <div
                key={i}
                className="card-hover flex gap-5 rounded-2xl border border-white/[0.07] bg-card p-8"
              >
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-[22px]"
                  style={{
                    background: `${f.color}18`,
                    border: `1px solid ${f.color}30`,
                    color: f.color,
                  }}
                >
                  {f.icon}
                </div>
                <div>
                  <h3 className="m-0 mb-2 text-lg font-semibold text-foreground">{f.title}</h3>
                  <p className="m-0 text-sm leading-relaxed text-foreground/50">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 用户评价 */}
      <section className="border-y border-white/[0.05] bg-primary/[0.04] px-6 py-20 pb-24">
        <div className="mx-auto max-w-[1280px]">
          <div className="mb-14 text-center">
            <p className="mb-3 font-mono text-[11px] uppercase tracking-[0.15em] text-accent">{t('home.communityEyebrow')}</p>
            <h2 className="m-0 font-display text-2xl font-bold text-foreground sm:text-3xl xl:text-4xl">
              {t('home.communityTitle')}
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {testimonials.map((tm, i) => (
              <div
                key={i}
                className="card-hover rounded-2xl border border-white/[0.07] bg-card p-7"
              >
                <div className="mb-5 flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full border-2 border-primary/30 bg-gradient-to-br from-[#7c3aed] to-[#06b6d4] text-sm font-bold text-white">
                    {tm.name[0]}
                  </div>
                  <div>
                    <p className="m-0 text-sm font-semibold text-foreground">{tm.name}</p>
                    <p className="m-0 font-mono text-xs text-muted-foreground">{tm.handle}</p>
                  </div>
                  <span className="ml-auto rounded-full border border-primary/30 bg-primary/[0.12] px-2.5 py-0.5 font-mono text-[10px] tracking-[0.08em] text-[#a78bfa]">
                    {tm.tier}
                  </span>
                </div>
                <p className="m-0 text-sm leading-relaxed text-foreground/65">"{tm.text}"</p>
                <div className="mt-4 flex gap-0.5">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <span key={s} className="text-sm text-amber-500">
                      ★
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-[800px] rounded-3xl border border-primary/25 bg-gradient-to-br from-primary/[0.15] to-accent/[0.08] px-10 py-16 text-center">
          <h2 className="m-0 mb-4 font-display text-3xl font-bold text-foreground sm:text-4xl xl:text-5xl">
            {t('home.ctaTitle')}
          </h2>
          <p className="mb-9 text-base leading-relaxed text-foreground/55">
            {t('home.ctaDesc')}
          </p>
          <Link
            href={user ? '/create' : '/login?mode=register'}
            className="inline-block rounded-[10px] bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-10 py-3.5 text-base font-semibold text-white shadow-glow"
          >
            {t('home.ctaButton')}
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] px-6 py-8">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-[#7c3aed] to-[#06b6d4] text-xs">
              ✦
            </div>
            <span className="font-display text-sm font-bold text-foreground">{t('nav.brand')}</span>
          </div>
          <p className="m-0 font-mono text-xs text-foreground/30">{t('home.footer')}</p>
          <div className="flex gap-5">
            {[
              { key: 'footerPrivacy', label: t('home.footerPrivacy') },
              { key: 'footerTerms', label: t('home.footerTerms') },
              { key: 'footerSupport', label: t('home.footerSupport') },
            ].map((l) => (
              <button
                key={l.key}
                className="bg-transparent text-xs text-foreground/35 transition hover:text-foreground/60"
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
