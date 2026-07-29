'use client';

import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';

export default function HomePage() {
  const { user, loading } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 via-white to-white">
      {/* 导航栏 */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🤝</span>
          <span className="text-xl font-bold text-brand-700">陪伴</span>
        </div>
        <div className="flex items-center gap-4">
          {loading ? null : user ? (
            <>
              <Link href="/chat" className="text-gray-600 hover:text-brand-700">
                我的角色
              </Link>
              <Link
                href="/create"
                className="rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                创建新角色
              </Link>
            </>
          ) : (
            <>
              <Link href="/login" className="text-gray-600 hover:text-brand-700">
                登录
              </Link>
              <Link
                href="/login?mode=register"
                className="rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                开始体验
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <h1 className="text-5xl font-bold tracking-tight text-gray-900">
          创作属于你的
          <span className="text-brand-600"> AI 陪伴人物</span>
        </h1>
        <p className="mt-6 text-lg text-gray-600 leading-relaxed">
          用模板快速定义人物的外貌、性格与关系。
          <br />
          以文字对话为核心，通过 AI 图片和视频让人物&ldquo;看得见&rdquo;，拥有更强的陪伴感。
        </p>
        <div className="mt-10 flex justify-center gap-4">
          <Link
            href={user ? '/create' : '/login?mode=register'}
            className="rounded-full bg-brand-600 px-8 py-3 text-base font-medium text-white shadow-lg hover:bg-brand-700 transition"
          >
            {user ? '创建新角色' : '免费开始'}
          </Link>
          {user && (
            <Link
              href="/chat"
              className="rounded-full border border-gray-300 px-8 py-3 text-base font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              继续对话
            </Link>
          )}
        </div>
      </section>

      {/* 价值卡片 */}
      <section className="max-w-5xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { icon: '✨', title: '专属感', desc: '人物由你塑造，名字、性格、外观和相处方式都可选择' },
          { icon: '💬', title: '陪伴感', desc: '人物会记住重要信息，在恰当的语境中回应与关心' },
          { icon: '📸', title: '可见感', desc: '角色自拍、场景图和动态问候让文字关系被看见' },
          { icon: '🌱', title: '成长感', desc: '共同经历沉淀为记忆、纪念册和角色关系变化' },
        ].map((v) => (
          <div key={v.title} className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="text-3xl mb-3">{v.icon}</div>
            <h3 className="font-semibold text-gray-900">{v.title}</h3>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">{v.desc}</p>
          </div>
        ))}
      </section>

      {/* 安全说明 */}
      <section className="max-w-3xl mx-auto px-6 py-12 text-center">
        <div className="rounded-2xl bg-gray-50 p-8">
          <h2 className="text-lg font-semibold text-gray-900">透明与安全</h2>
          <p className="mt-3 text-sm text-gray-600 leading-relaxed">
            所有角色均为 AI，不具备真实意识。我们保护你的私密对话和图片，
            设置年龄、内容与情感安全边界。你可以随时查看、编辑或删除角色的记忆。
          </p>
        </div>
      </section>

      <footer className="text-center py-8 text-sm text-gray-400">
        © 2025 陪伴平台 · 这是一个 AI 产品，角色不暗示真实人际关系
      </footer>
    </div>
  );
}
