'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import type { Character, Message } from '@companion/shared';
import { MessageRole, MessageFeedback } from '@companion/shared';

export default function ChatPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selected, setSelected] = useState<Character | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      api.get<{ items?: Character[] } | Character[]>('/characters').then((res) => {
        const list = Array.isArray(res) ? res : res.items || [];
        setCharacters(list);
        if (list.length > 0) selectCharacter(list[0]);
      });
    }
  }, [user]);

  const selectCharacter = async (char: Character) => {
    setSelected(char);
    const res = await api.get<{ conversation_id: string | null; messages: Message[] }>(
      `/conversations/${char.id}/messages`,
    );
    setMessages(res.messages);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamText]);

  const handleSend = async () => {
    if (!selected || !input.trim() || streaming) return;
    const content = input.trim();
    setInput('');

    // 乐观更新：先显示用户消息
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      role: MessageRole.USER,
      content,
      feedback: MessageFeedback.NONE,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    // 流式接收回复
    setStreaming(true);
    setStreamText('');
    try {
      await api.stream(
        `/conversations/${selected.id}/messages`,
        { content },
        (token) => setStreamText((prev) => prev + token),
      );
      // 流结束后刷新消息列表
      const res = await api.get<{ messages: Message[] }>(`/conversations/${selected.id}/messages`);
      setMessages(res.messages);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: MessageRole.ASSISTANT,
          content: `[错误] ${err}`,
          feedback: MessageFeedback.NONE,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setStreamText('');
      setStreaming(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">加载中...</div>;
  if (!user) return null;

  if (characters.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-gray-500">你还没有创建任何角色</p>
        <button
          onClick={() => router.push('/create')}
          className="rounded-full bg-brand-600 px-6 py-2 text-white hover:bg-brand-700"
        >
          创建第一个角色
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 侧边栏：角色列表 */}
      <aside className="w-64 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-gray-900">我的角色</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {characters.map((c) => (
            <button
              key={c.id}
              onClick={() => selectCharacter(c)}
              className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition ${
                selected?.id === c.id ? 'bg-brand-50 border-l-4 border-brand-600' : ''
              }`}
            >
              <div className="font-medium text-gray-900">{c.name}</div>
              <div className="text-xs text-gray-400 truncate">
                {c.companion_preference || '点击开始对话'}
              </div>
            </button>
          ))}
        </div>
        <div className="p-3 border-t">
          <button
            onClick={() => router.push('/create')}
            className="w-full rounded-lg border border-dashed border-gray-300 py-2 text-sm text-gray-500 hover:border-brand-400 hover:text-brand-600 transition"
          >
            + 创建新角色
          </button>
        </div>
      </aside>

      {/* 聊天主区域 */}
      <main className="flex-1 flex flex-col">
        {selected && (
          <header className="px-6 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
            <div>
              <h1 className="font-semibold text-gray-900">{selected.name}</h1>
              <p className="text-xs text-gray-400">AI 陪伴角色 · 不具备真实意识</p>
            </div>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
              这不是真人
            </span>
          </header>
        )}

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === MessageRole.USER ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-2.5 ${
                  msg.role === MessageRole.USER
                    ? 'bg-brand-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}

          {/* 流式回复 */}
          {streaming && streamText && (
            <div className="flex justify-start">
              <div className="max-w-[70%] rounded-2xl px-4 py-2.5 bg-white border border-gray-200">
                <p className="text-sm whitespace-pre-wrap">
                  {streamText}
                  <span className="inline-block w-1.5 h-4 bg-brand-400 ml-0.5 animate-pulse" />
                </p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入栏 */}
        <div className="border-t border-gray-200 bg-white px-4 py-3">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder={`对 ${selected?.name || '角色'} 说点什么...`}
              disabled={streaming}
              className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={streaming || !input.trim()}
              className="rounded-full bg-brand-600 px-6 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition"
            >
              {streaming ? '回复中...' : '发送'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
