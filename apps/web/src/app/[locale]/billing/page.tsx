'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api, translateError } from '@/lib/api';

interface LedgerItem {
  id: string;
  type: string;
  note?: string;
  amount: number;
  created_at: string;
}

const LOCALE_MAP: Record<string, string> = { en: 'en-US', zh: 'zh-CN', ja: 'ja-JP', es: 'es-ES' };

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
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        {t('common.loading')}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-bold text-gray-900">{t('billing.title')}</h1>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* 积分卡片 */}
        <div className="bg-gradient-to-r from-brand-500 to-brand-700 rounded-2xl p-6 text-white">
          <p className="text-sm opacity-90">{t('billing.currentCredits')}</p>
          <p className="text-4xl font-bold mt-1">{user?.credits_balance ?? 0}</p>
          <p className="text-sm opacity-75 mt-2">
            {t('billing.plan')}：{user?.subscription_tier || t('billing.freeTier')}
          </p>
        </div>

        {/* 订阅与积分包 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="font-bold text-gray-900">{t('billing.subscriptionTitle')}</h3>
            <p className="text-sm text-gray-500 mt-1">{t('billing.subscriptionDesc')}</p>
            <button
              onClick={() => checkout('subscription')}
              disabled={processing}
              className="mt-4 w-full rounded-lg bg-brand-600 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50"
            >
              {t('billing.subscribe')}
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="font-bold text-gray-900">{t('billing.creditsPackTitle')}</h3>
            <p className="text-sm text-gray-500 mt-1">{t('billing.creditsPackDesc')}</p>
            <button
              onClick={() => checkout('credits')}
              disabled={processing}
              className="mt-4 w-full rounded-lg border border-brand-600 text-brand-600 py-2 font-medium hover:bg-brand-50 disabled:opacity-50"
            >
              {t('billing.buyCredits')}
            </button>
          </div>
        </div>

        {/* 消费明细 */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">{t('billing.ledgerTitle')}</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {ledger.length === 0 ? (
              <p className="px-6 py-8 text-center text-sm text-gray-400">{t('billing.ledgerEmpty')}</p>
            ) : (
              ledger.map((item) => (
                <div key={item.id} className="flex items-center justify-between px-6 py-3">
                  <div>
                    <p className="text-sm text-gray-900">{item.note || item.type}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(item.created_at).toLocaleString(dateLocale)}
                    </p>
                  </div>
                  <span className={`font-medium ${item.amount > 0 ? 'text-green-600' : 'text-gray-900'}`}>
                    {item.amount > 0 ? '+' : ''}
                    {item.amount}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
