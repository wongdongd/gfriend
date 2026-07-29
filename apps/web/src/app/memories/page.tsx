'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import type { Memory } from '@companion/shared';

export default function MemoriesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (user) loadMemories();
  }, [user, filter]);

  const loadMemories = async () => {
    const path = filter ? `?status=${filter}` : '';
    const res = await api.get<{ items: Memory[] }>(`/memories${path}`);
    setMemories(res.items);
  };

  const handleAction = async (id: string, action: 'confirmed' | 'rejected' | 'delete') => {
    if (action === 'delete') {
      await api.delete(`/memories/${id}`);
    } else {
      await api.patch(`/memories/${id}`, { status: action });
    }
    loadMemories();
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">加载中...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">记忆中心</h1>
          <button onClick={() => router.push('/chat')} className="text-sm text-brand-600 hover:text-brand-700">
            返回对话
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 过滤 */}
        <div className="flex gap-2 mb-6">
          {[{ v: '', l: '全部' }, { v: 'candidate', l: '待确认' }, { v: 'confirmed', l: '已确认' }].map((f) => (
            <button
              key={f.v}
              onClick={() => setFilter(f.v)}
              className={`px-3 py-1 rounded-full text-sm ${
                filter === f.v ? 'bg-brand-600 text-white' : 'bg-white border border-gray-200 text-gray-600'
              }`}
            >
              {f.l}
            </button>
          ))}
        </div>

        {/* 记忆卡片 */}
        {memories.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p>还没有记忆</p>
            <p className="text-sm mt-1">角色会在对话中记住你提到的重要信息</p>
          </div>
        ) : (
          <div className="space-y-3">
            {memories.map((m) => (
              <div key={m.id} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
                <p className="text-gray-900">{m.content}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    m.status === 'confirmed' ? 'bg-green-100 text-green-700' :
                    m.status === 'candidate' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-500'
                  }`}>
                    {m.status === 'confirmed' ? '已确认' : m.status === 'candidate' ? '待确认' : m.status}
                  </span>
                  <div className="flex gap-2">
                    {m.status === 'candidate' && (
                      <>
                        <button
                          onClick={() => handleAction(m.id, 'confirmed')}
                          className="text-xs text-green-600 hover:text-green-700"
                        >
                          确认
                        </button>
                        <button
                          onClick={() => handleAction(m.id, 'rejected')}
                          className="text-xs text-gray-400 hover:text-gray-600"
                        >
                          拒绝
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => handleAction(m.id, 'delete')}
                      className="text-xs text-red-400 hover:text-red-600"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <p className="mt-8 text-center text-xs text-gray-400">
          角色只会使用你确认过的记忆。你可以随时编辑或删除。
        </p>
      </div>
    </div>
  );
}
