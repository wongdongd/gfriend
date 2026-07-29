'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import type { CreditLedgerEntry } from '@companion/shared';

export default function BillingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [ledger, setLedger] = useState<CreditLedgerEntry[]>([]);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      api.get<{ items: CreditLedgerEntry[] }>('/billing/credits/ledger').then((res) => setLedger(res.items));
    }
  }, [user]);

  const handleCheckout = async (type: 'subscription' | 'credits') => {
    setCheckoutLoading(true);
    try {
      const res = await api.post<{ checkout_url: string }>('/billing/checkout', {
        order_type: type,
        sku_code: type === 'subscription' ? 'companion_monthly' : 'credits_100',
      });
      window.location.href = res.checkout_url;
    } catch (err) {
      alert(err instanceof Error ? err.message : '支付发起失败');
    } finally {
      setCheckoutLoading(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">加载中...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-bold text-gray-900">钱包与订阅</h1>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* 余额 */}
        <div className="bg-gradient-to-r from-brand-500 to-brand-700 rounded-2xl p-6 text-white">
          <p className="text-sm opacity-90">当前积分</p>
          <p className="text-4xl font-bold mt-1">{user?.credits_balance ?? 0}</p>
          <p className="text-sm opacity-75 mt-2">
            套餐：{user?.subscription_tier || '免费体验'}
          </p>
        </div>

        {/* 套餐 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="font-bold text-gray-900">陪伴订阅</h3>
            <p className="text-sm text-gray-500 mt-1">多个角色、更大记忆容量、每月图片额度</p>
            <button
              onClick={() => handleCheckout('subscription')}
              disabled={checkoutLoading}
              className="mt-4 w-full rounded-lg bg-brand-600 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50"
            >
              订阅
            </button>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="font-bold text-gray-900">积分包</h3>
            <p className="text-sm text-gray-500 mt-1">100 积分，用于图片和视频生成</p>
            <button
              onClick={() => handleCheckout('credits')}
              disabled={checkoutLoading}
              className="mt-4 w-full rounded-lg border border-brand-600 text-brand-600 py-2 font-medium hover:bg-brand-50 disabled:opacity-50"
            >
              购买积分
            </button>
          </div>
        </div>

        {/* 流水 */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">消费流水</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {ledger.length === 0 ? (
              <p className="px-6 py-8 text-center text-sm text-gray-400">暂无记录</p>
            ) : (
              ledger.map((l) => (
                <div key={l.id} className="flex items-center justify-between px-6 py-3">
                  <div>
                    <p className="text-sm text-gray-900">{l.note || l.type}</p>
                    <p className="text-xs text-gray-400">{new Date(l.created_at).toLocaleString('zh-CN')}</p>
                  </div>
                  <span className={`font-medium ${l.amount > 0 ? 'text-green-600' : 'text-gray-900'}`}>
                    {l.amount > 0 ? '+' : ''}{l.amount}
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
