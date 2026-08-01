'use client';

import { useEffect, useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api, translateError } from '@/lib/api';
import Navbar from '@/components/Navbar';

interface LedgerItem {
  id: string;
  type: string;
  note?: string;
  amount: number;
  created_at: string;
}

const LOCALE_MAP: Record<string, string> = { en: 'en-US', zh: 'zh-CN', ja: 'ja-JP', es: 'es-ES' };

const TIERS = [
  {
    code: 'free',
    nameKey: 'tierFreeName',
    priceKey: 'tierFreePrice',
    periodKey: 'tierFreePeriod',
    ctaKey: 'tierFreeCta',
    color: '#6b6880',
    featureKeys: ['featureFree1', 'featureFree2', 'featureFree3', 'featureFree4'],
  },
  {
    code: 'creator',
    nameKey: 'tierCreatorName',
    priceKey: 'tierCreatorPrice',
    periodKey: 'tierCreatorPeriod',
    ctaKey: 'tierCreatorCta',
    color: '#06b6d4',
    featureKeys: ['featureCreator1', 'featureCreator2', 'featureCreator3', 'featureCreator4', 'featureCreator5'],
    popular: true,
  },
  {
    code: 'studio',
    nameKey: 'tierStudioName',
    priceKey: 'tierStudioPrice',
    periodKey: 'tierStudioPeriod',
    ctaKey: 'tierStudioCta',
    color: '#7c3aed',
    featureKeys: ['featureStudio1', 'featureStudio2', 'featureStudio3', 'featureStudio4', 'featureStudio5', 'featureStudio6'],
  },
];

export default function BillingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const t = useTranslations();
  const locale = useLocale();
  const dateLocale = LOCALE_MAP[locale] || 'en-US';

  const [ledger, setLedger] = useState<LedgerItem[]>([]);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      api.get<{ items: LedgerItem[] }>('/billing/credits/ledger').then((res) => setLedger(res.items));
    }
  }, [user]);

  const checkout = async (orderType: string) => {
    setProcessing(true);
    try {
      const res = await api.post<{ checkout_url: string }>('/billing/checkout', {
        order_type: orderType,
        sku_code: orderType === 'subscription' ? 'companion_monthly' : 'credits_100',
      });
      window.location.href = res.checkout_url;
    } catch (err) {
      alert(translateError(t, err));
    } finally {
      setProcessing(false);
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

      {/* 积分余额 */}
      <section className="mesh-bg px-6 pb-12 pt-32">
        <div className="mx-auto max-w-[1280px]">
          <div className="mb-8 text-center">
            <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.15em] text-accent">
              {t('billing.balanceEyebrow')}
            </p>
            <h1 className="font-display m-0 text-4xl font-bold text-foreground">
              {t('billing.balanceTitle')}
            </h1>
          </div>

          <div className="mx-auto max-w-[560px] rounded-3xl border border-primary/30 bg-gradient-to-br from-primary/[0.18] to-accent/[0.1] p-8 text-center shadow-glow">
            <p className="m-0 font-mono text-xs uppercase tracking-[0.1em] text-foreground/50">
              {t('billing.currentBalanceLabel')}
            </p>
            <p className="m-0 mt-2 font-display text-5xl font-bold text-[#a78bfa]">
              {user.credits_balance ?? 0}
            </p>
            <p className="m-0 mt-2 text-sm text-foreground/50">
              {t('billing.creditsUnit')} · {user.subscription_tier || t('billing.tierFreeName')} {t('billing.tier')}
            </p>
            <button
              onClick={() => checkout('credits')}
              disabled={processing}
              className="mt-6 rounded-lg border border-accent/40 bg-accent/10 px-6 py-2.5 text-sm font-semibold text-accent transition hover:bg-accent/20 disabled:opacity-50"
            >
              {processing ? t('billing.processing') : t('billing.buyCreditsButton')}
            </button>
          </div>
        </div>
      </section>

      {/* 定价方案 */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-[1280px]">
          <div className="mb-12 text-center">
            <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.15em] text-accent">
              {t('billing.pricingEyebrow')}
            </p>
            <h2 className="font-display m-0 mb-3 text-3xl font-bold text-foreground sm:text-4xl">
              {t('billing.pricingTitle')}
            </h2>
            <p className="mx-auto max-w-[480px] text-base text-foreground/50">
              {t('billing.pricingSubtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {TIERS.map((tier) => (
              <div
                key={tier.code}
                className={`relative flex flex-col rounded-2xl border p-7 ${
                  tier.popular
                    ? 'border-primary/50 bg-primary/[0.06]'
                    : 'border-white/[0.07] bg-card'
                }`}
              >
                {tier.popular && (
                  <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-3 py-0.5 font-mono text-[10px] tracking-[0.08em] text-white">
                    {t('billing.mostPopular')}
                  </span>
                )}

                <h3 className="m-0 text-lg font-bold text-foreground">{t(`billing.${tier.nameKey}`)}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span
                    className="font-display text-4xl font-bold"
                    style={{ color: tier.color }}
                  >
                    {t(`billing.${tier.priceKey}`)}
                  </span>
                  <span className="text-sm text-foreground/40">{t(`billing.${tier.periodKey}`)}</span>
                </div>

                <ul className="mt-5 flex-1 space-y-2.5">
                  {tier.featureKeys.map((fk, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-foreground/65">
                      <span
                        className="text-xs"
                        style={{ color: tier.color }}
                      >
                        ✦
                      </span>
                      {t(`billing.${fk}`)}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => tier.code !== 'free' && checkout('subscription')}
                  disabled={processing || tier.code === 'free'}
                  className={`mt-6 rounded-lg py-2.5 text-sm font-semibold transition disabled:cursor-default ${
                    tier.popular
                      ? 'bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] text-white hover:opacity-90'
                      : tier.code === 'free'
                        ? 'border border-white/10 text-foreground/40'
                        : 'border text-white transition hover:opacity-90'
                  }`}
                  style={
                    tier.code !== 'free' && !tier.popular
                      ? {
                          background: `linear-gradient(135deg, ${tier.color}, ${tier.color}dd)`,
                          borderColor: tier.color,
                        }
                      : {}
                  }
                >
                  {t(`billing.${tier.ctaKey}`)}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 消费明细 */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-[1280px]">
          <h2 className="font-display m-0 mb-6 text-2xl font-bold text-foreground">
            {t('billing.creditHistory')}
          </h2>
          <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-card">
            <div className="border-b border-white/[0.06] px-6 py-4">
              <h3 className="m-0 font-semibold text-foreground">{t('billing.ledgerTitle')}</h3>
            </div>
            <div className="divide-y divide-white/[0.04]">
              {ledger.length === 0 ? (
                <p className="px-6 py-8 text-center text-sm text-foreground/40">
                  {t('billing.ledgerEmpty')}
                </p>
              ) : (
                ledger.map((item) => (
                  <div key={item.id} className="flex items-center justify-between px-6 py-3">
                    <div>
                      <p className="m-0 text-sm text-foreground">{item.note || item.type}</p>
                      <p className="m-0 font-mono text-xs text-foreground/30">
                        {new Date(item.created_at).toLocaleString(dateLocale)}
                      </p>
                    </div>
                    <span
                      className={`font-mono font-medium ${
                        item.amount > 0 ? 'text-[#34d399]' : 'text-foreground/60'
                      }`}
                    >
                      {item.amount > 0 ? '+' : ''}
                      {item.amount}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
