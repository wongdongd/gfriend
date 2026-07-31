'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api, translateError } from '@/lib/api';

const RELATIONSHIPS = [
  { code: 'friend', icon: '🤝' },
  { code: 'lover', icon: '💕' },
  { code: 'healer', icon: '🌙' },
  { code: 'study_buddy', icon: '📚' },
  { code: 'listener', icon: '👂' },
  { code: 'original', icon: '✨' },
];

const PERSONALITIES = [
  { code: 'gentle', icon: '🌿' },
  { code: 'energetic', icon: '⚡' },
  { code: 'calm', icon: '🧊' },
  { code: 'humorous', icon: '😏' },
  { code: 'quiet_healing', icon: '🍃' },
];

const STYLES = [
  { code: 'cinematic' },
  { code: 'fresh_life' },
  { code: 'fashion_mag' },
  { code: '3d_anime' },
  { code: 'anime' },
  { code: 'retro_film' },
  { code: 'ink_wash' },
];

export default function CreatePage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const t = useTranslations();

  const [step, setStep] = useState(1);
  const [relationship, setRelationship] = useState('');
  const [personality, setPersonality] = useState('');
  const [style, setStyle] = useState('');
  const [name, setName] = useState('');
  const [preference, setPreference] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  const canNext = () => {
    if (step === 1) return !!relationship;
    if (step === 2) return !!personality;
    if (step === 3) return !!style;
    return step === 4 && name.trim().length > 0;
  };

  const create = async () => {
    setCreating(true);
    try {
      await api.post('/characters', {
        name: name.trim(),
        companion_preference: preference.trim() || null,
        relationship_template_code: relationship,
        personality_template_code: personality,
        visual_style_code: style,
      });
      router.push('/chat');
    } catch (err) {
      alert(translateError(t, err));
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        {t('common.loading')}
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 to-white">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* 步骤指示器 */}
        <div className="flex items-center justify-between mb-8">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= s ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-400'
                }`}
              >
                {s}
              </div>
              {s < 4 && (
                <div className={`flex-1 h-0.5 mx-2 ${step > s ? 'bg-brand-600' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          {/* 第 1 步：关系 */}
          {step === 1 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">{t('create.chooseRelationship')}</h2>
              <p className="text-sm text-gray-500 mb-6">{t('create.relationshipDesc')}</p>
              <div className="grid grid-cols-2 gap-3">
                {RELATIONSHIPS.map((r) => (
                  <button
                    key={r.code}
                    onClick={() => setRelationship(r.code)}
                    className={`text-left p-4 rounded-xl border-2 transition ${
                      relationship === r.code
                        ? 'border-brand-600 bg-brand-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">{r.icon}</div>
                    <div className="font-medium text-gray-900">
                      {t(`create.relationships.${r.code}.label`)}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {t(`create.relationships.${r.code}.desc`)}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 第 2 步：性格 */}
          {step === 2 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">{t('create.choosePersonality')}</h2>
              <p className="text-sm text-gray-500 mb-6">{t('create.personalityDesc')}</p>
              <div className="space-y-2">
                {PERSONALITIES.map((p) => (
                  <button
                    key={p.code}
                    onClick={() => setPersonality(p.code)}
                    className={`w-full text-left p-4 rounded-xl border-2 transition ${
                      personality === p.code
                        ? 'border-brand-600 bg-brand-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900">
                      {p.icon} {t(`create.personalities.${p.code}.label`)}
                    </div>
                    <div className="text-sm text-gray-500 mt-0.5">
                      {t(`create.personalities.${p.code}.desc`)}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 第 3 步：风格 */}
          {step === 3 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">{t('create.chooseStyle')}</h2>
              <p className="text-sm text-gray-500 mb-6">{t('create.styleDesc')}</p>
              <div className="grid grid-cols-2 gap-3">
                {STYLES.map((s) => (
                  <button
                    key={s.code}
                    onClick={() => setStyle(s.code)}
                    className={`p-4 rounded-xl border-2 transition text-center ${
                      style === s.code
                        ? 'border-brand-600 bg-brand-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900 text-sm">
                      {t(`create.styles.${s.code}.label`)}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 第 4 步：名字 */}
          {step === 4 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">{t('create.nameTitle')}</h2>
              <p className="text-sm text-gray-500 mb-6">{t('create.nameDesc')}</p>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('create.nameLabel')}
                  </label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={64}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
                    placeholder={t('create.namePlaceholder')}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('create.preferenceLabel')}{' '}
                    <span className="text-gray-400">{t('create.preferenceOptional')}</span>
                  </label>
                  <textarea
                    value={preference}
                    onChange={(e) => setPreference(e.target.value)}
                    rows={3}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none resize-none"
                    placeholder={t('create.preferencePlaceholder')}
                  />
                </div>
              </div>
            </div>
          )}

          {/* 底部按钮 */}
          <div className="flex justify-between mt-8">
            <button
              onClick={() => (step > 1 ? setStep(step - 1) : router.back())}
              className="px-4 py-2 text-gray-600 hover:text-gray-900"
            >
              {step > 1 ? t('create.prev') : t('common.back')}
            </button>
            {step < 4 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!canNext()}
                className="rounded-full bg-brand-600 px-8 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {t('create.next')}
              </button>
            ) : (
              <button
                onClick={create}
                disabled={!canNext() || creating}
                className="rounded-full bg-brand-600 px-8 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {creating ? t('create.creating') : t('create.startAcquaintance')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
