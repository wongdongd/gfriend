'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api, translateError } from '@/lib/api';

type MessageRole = 'user' | 'assistant' | 'system';
type FeedbackType = 'none' | 'like' | 'dislike' | 'adjust_tone';

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  feedback: FeedbackType;
  created_at: string;
}

interface Character {
  id: string;
  name: string;
  companion_preference?: string | null;
}

export default function ChatPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const t = useTranslations();

  const [characters, setCharacters] = useState<Character[]>([]);
  const [current, setCurrent] = useState<Character | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [replying, setReplying] = useState(false);
  const [streamText, setStreamText] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  // 未登录跳转
  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  // 加载角色列表
  useEffect(() => {
    if (user) {
      api.get<Character[]>('/characters').then((data) => {
        const list = Array.isArray(data) ? data : (data as { items?: Character[] }).items || [];
        setCharacters(list);
        if (list.length > 0) selectCharacter(list[0]);
      });
    }
  }, [user]);

  const selectCharacter = async (c: Character) => {
    setCurrent(c);
    const res = await api.get<{ messages: Message[] }>(`/conversations/${c.id}/messages`);
    setMessages(res.messages);
  };

  // 自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamText]);

  const send = async () => {
    if (!current || !input.trim() || replying) return;
    const content = input.trim();
    setInput('');

    const temp: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      feedback: 'none',
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, temp]);
    setReplying(true);
    setStreamText('');

    try {
      let accumulated = '';
      const doneData = await api.stream(
        `/conversations/${current.id}/messages`,
        { content },
        (token) => {
          accumulated += token;
          setStreamText(accumulated);
        },
      );
      // 使用后端返回的 message_id 作为最终消息 ID，本地拼接避免重新拉取全部消息
      const messageId = (doneData.message_id as string) || `msg-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: messageId,
          role: 'assistant',
          content: accumulated,
          feedback: 'none',
          created_at: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `${t('chat.errorPrefix')}${translateError(t, err)}`,
          feedback: 'none',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setStreamText('');
      setReplying(false);
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

  if (characters.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-gray-500">{t('chat.noCharacters')}</p>
        <button
          onClick={() => router.push('/create')}
          className="rounded-full bg-brand-600 px-6 py-2 text-white hover:bg-brand-700"
        >
          {t('chat.createFirst')}
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 角色侧边栏 */}
      <aside className="w-64 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-gray-900">{t('chat.myCharacters')}</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {characters.map((c) => (
            <button
              key={c.id}
              onClick={() => selectCharacter(c)}
              className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition ${
                current?.id === c.id ? 'bg-brand-50 border-l-4 border-brand-600' : ''
              }`}
            >
              <div className="font-medium text-gray-900">{c.name}</div>
              <div className="text-xs text-gray-400 truncate">
                {c.companion_preference || t('chat.clickToChat')}
              </div>
            </button>
          ))}
        </div>
        <div className="p-3 border-t">
          <button
            onClick={() => router.push('/create')}
            className="w-full rounded-lg border border-dashed border-gray-300 py-2 text-sm text-gray-500 hover:border-brand-400 hover:text-brand-600 transition"
          >
            + {t('chat.createNew')}
          </button>
        </div>
      </aside>

      {/* 聊天主区 */}
      <main className="flex-1 flex flex-col">
        {current && (
          <header className="px-6 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
            <div>
              <h1 className="font-semibold text-gray-900">{current.name}</h1>
              <p className="text-xs text-gray-400">{t('chat.aiTag')}</p>
            </div>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
              {t('chat.notReal')}
            </span>
          </header>
        )}

        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-2.5 ${
                  m.role === 'user'
                    ? 'bg-brand-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{m.content}</p>
              </div>
            </div>
          ))}

          {replying && streamText && (
            <div className="flex justify-start">
              <div className="max-w-[70%] rounded-2xl px-4 py-2.5 bg-white border border-gray-200">
                <p className="text-sm whitespace-pre-wrap">
                  {streamText}
                  <span className="inline-block w-1.5 h-4 bg-brand-400 ml-0.5 animate-pulse" />
                </p>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="border-t border-gray-200 bg-white px-4 py-3">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
              placeholder={t('chat.inputPlaceholder', { name: current?.name ?? '' })}
              disabled={replying}
              className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none disabled:opacity-50"
            />
            <button
              onClick={send}
              disabled={replying || !input.trim()}
              className="rounded-full bg-brand-600 px-6 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition"
            >
              {replying ? t('chat.replying') : t('chat.send')}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
