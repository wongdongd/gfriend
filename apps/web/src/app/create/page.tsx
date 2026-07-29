'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import type { Character } from '@companion/shared';

const RELATIONSHIPS = [
  { code: 'friend', label: '朋友', icon: '🤝', desc: '互相支持的日常伙伴' },
  { code: 'lover', label: '恋人', icon: '💕', desc: '亲密浪漫的关系' },
  { code: 'healer', label: '治愈伙伴', icon: '🌙', desc: '温柔倾听与安慰' },
  { code: 'study_buddy', label: '学习搭子', icon: '📚', desc: '一起专注与进步' },
  { code: 'listener', label: '倾听者', icon: '👂', desc: '安静地听你说' },
  { code: 'original', label: '原创角色', icon: '✨', desc: '完全自定义' },
];

const PERSONALITIES = [
  { code: 'gentle', label: '温柔可靠', desc: '温暖、耐心、让人安心' },
  { code: 'energetic', label: '活泼元气', desc: '开朗、热情、充满活力' },
  { code: 'calm', label: '冷静理性', desc: '沉稳、客观、思路清晰' },
  { code: 'humorous', label: '幽默毒舌', desc: '有趣、犀利但不伤人' },
  { code: 'quiet_healing', label: '安静治愈', desc: '轻柔、慢节奏、治愈感' },
];

const STYLES = [
  { code: 'cinematic', label: '写实电影感' },
  { code: 'fresh_life', label: '清新生活' },
  { code: 'fashion_mag', label: '时尚杂志' },
  { code: '3d_anime', label: '3D 动画' },
  { code: 'anime', label: '日系插画' },
  { code: 'retro_film', label: '复古胶片' },
  { code: 'ink_wash', label: '国风水墨' },
];

export default function CreatePage() {
  const router = useRouter();
  const { user, loading } = useAuth();
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

  const canProceed = () => {
    if (step === 1) return !!relationship;
    if (step === 2) return !!personality;
    if (step === 3) return !!style;
    if (step === 4) return name.trim().length > 0;
    return false;
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      const char = await api.post<Character>('/characters', {
        name: name.trim(),
        companion_preference: preference.trim() || null,
        relationship_template_code: relationship,
        personality_template_code: personality,
        visual_style_code: style,
      });
      router.push('/chat');
    } catch (err) {
      alert(err instanceof Error ? err.message : '创建失败');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">加载中...</div>;
  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 to-white">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* 进度条 */}
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
              {s < 4 && <div className={`flex-1 h-0.5 mx-2 ${step > s ? 'bg-brand-600' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          {/* Step 1: 关系 */}
          {step === 1 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">选择你们的关系</h2>
              <p className="text-sm text-gray-500 mb-6">这决定了角色与你互动的基本方式</p>
              <div className="grid grid-cols-2 gap-3">
                {RELATIONSHIPS.map((r) => (
                  <button
                    key={r.code}
                    onClick={() => setRelationship(r.code)}
                    className={`text-left p-4 rounded-xl border-2 transition ${
                      relationship === r.code ? 'border-brand-600 bg-brand-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">{r.icon}</div>
                    <div className="font-medium text-gray-900">{r.label}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{r.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: 人格 */}
          {step === 2 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">选择 TA 的性格</h2>
              <p className="text-sm text-gray-500 mb-6">原型决定默认表达方式与互动边界</p>
              <div className="space-y-2">
                {PERSONALITIES.map((p) => (
                  <button
                    key={p.code}
                    onClick={() => setPersonality(p.code)}
                    className={`w-full text-left p-4 rounded-xl border-2 transition ${
                      personality === p.code ? 'border-brand-600 bg-brand-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900">{p.label}</div>
                    <div className="text-sm text-gray-500 mt-0.5">{p.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: 外观风格 */}
          {step === 3 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">选择外观风格</h2>
              <p className="text-sm text-gray-500 mb-6">角色生成的图片会使用这个风格</p>
              <div className="grid grid-cols-2 gap-3">
                {STYLES.map((s) => (
                  <button
                    key={s.code}
                    onClick={() => setStyle(s.code)}
                    className={`p-4 rounded-xl border-2 transition text-center ${
                      style === s.code ? 'border-brand-600 bg-brand-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900 text-sm">{s.label}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 4: 命名与偏好 */}
          {step === 4 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">给 TA 起个名字</h2>
              <p className="text-sm text-gray-500 mb-6">以及你希望 TA 怎样陪伴你</p>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">名字</label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={64}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
                    placeholder="给你的角色起个名字"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    希望 TA 怎样陪伴你 <span className="text-gray-400">（可选）</span>
                  </label>
                  <textarea
                    value={preference}
                    onChange={(e) => setPreference(e.target.value)}
                    rows={3}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none resize-none"
                    placeholder="例如：在我难过的时候安静地陪我，在我开心时一起庆祝"
                  />
                </div>
              </div>
            </div>
          )}

          {/* 导航按钮 */}
          <div className="flex justify-between mt-8">
            <button
              onClick={() => (step > 1 ? setStep(step - 1) : router.back())}
              className="px-4 py-2 text-gray-600 hover:text-gray-900"
            >
              {step > 1 ? '上一步' : '返回'}
            </button>
            {step < 4 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!canProceed()}
                className="rounded-full bg-brand-600 px-8 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                下一步
              </button>
            ) : (
              <button
                onClick={handleCreate}
                disabled={!canProceed() || creating}
                className="rounded-full bg-brand-600 px-8 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {creating ? '创建中...' : '开始相识'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
