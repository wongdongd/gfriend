'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import { api, translateError } from '@/lib/api';
import Navbar from '@/components/Navbar';
import ChatLayout from '@/components/chat/ChatLayout';
import type { ReferenceImage } from '@/components/chat/ReferencePanel';
import type { Message as Msg, Attachment, GenerationState } from '@/types/chat';

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
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [replying, setReplying] = useState(false);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [pendingAttachments, setPendingAttachments] = useState<Attachment[]>([]);
  const [referenceImages, setReferenceImages] = useState<ReferenceImage[]>([]);
  // 追踪活跃的 polling timers，用于组件卸载时清理
  const pollTimersRef = useRef<Set<ReturnType<typeof setInterval>>>(new Set());

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      api.get<Character[]>('/characters').then((data) => {
        const list = Array.isArray(data) ? data : (data as { items?: Character[] }).items || [];
        setCharacters(list);
        // 优先从 URL ?character_id= 读取指定角色，否则取列表第一个
        const params = new URLSearchParams(window.location.search);
        const requestedId = params.get('character_id');
        const initial = (requestedId && list.find((c) => c.id === requestedId)) || list[0];
        if (initial) selectCharacter(initial);
      });
    }
  }, [user]);

  // 组件卸载时清理所有活跃的轮询 timer
  useEffect(() => {
    const timers = pollTimersRef.current;
    return () => {
      timers.forEach((t) => clearInterval(t));
      timers.clear();
    };
  }, []);

  const selectCharacter = async (c: Character) => {
    setCurrent(c);
    setReferenceImages([]);
    const res = await api.get<{ messages: Msg[] }>(`/conversations/${c.id}/messages`);
    setMessages(res.messages);
  };

  const send = async (rawText?: string, rawAttachments?: Attachment[]) => {
    const content = (rawText ?? input).trim();
    const attachments = rawAttachments ?? pendingAttachments;
    if (!current || !content || replying) return;
    setInput('');
    setPendingAttachments([]);
    setReplying(true);

    const attachmentIds: string[] = attachments
      .map((a) => a.asset_id)
      .filter((id): id is string => Boolean(id));

    const temp: Msg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      feedback: 'none',
      created_at: new Date().toISOString(),
      attachments,
    };
    setMessages((prev) => [...prev, temp]);

    try {
      let accumulated = '';
      const replyId = `reply-${Date.now()}`;
      setStreamingId(replyId);
      // SSE 流式渲染优化：用 ref 累积内容，按帧（~16ms）批量更新 state，
      // 避免每个 token 触发一次完整 MessageList 重渲染。
      let lastUpdate = 0;
      const BATCH_MS = 40; // 约 25 fps，对文本流绰绰有余
      const doneData = await api.stream(
        `/conversations/${current!.id}/messages`,
        { content, attachment_ids: attachmentIds },
        (token) => {
          accumulated += token;
          const now = Date.now();
          if (now - lastUpdate < BATCH_MS) return; // 跳过，等下一帧
          lastUpdate = now;
          const snapshot = accumulated;
          setMessages((prev) => {
            const exists = prev.some((m) => m.id === replyId);
            if (exists) {
              return prev.map((m) => (m.id === replyId ? { ...m, content: snapshot } : m));
            }
            return [
              ...prev,
              {
                id: replyId,
                role: 'assistant',
                content: snapshot,
                feedback: 'none',
                created_at: new Date().toISOString(),
              },
            ];
          });
        },
      );
      // 流结束后写入最终完整内容
      setMessages((prev) => {
        const exists = prev.some((m) => m.id === replyId);
        if (exists) {
          return prev.map((m) => (m.id === replyId ? { ...m, content: accumulated } : m));
        }
        return [
          ...prev,
          {
            id: replyId,
            role: 'assistant',
            content: accumulated,
            feedback: 'none',
            created_at: new Date().toISOString(),
          },
        ];
      });
      const messageId = (doneData.message_id as string) || replyId;
      setMessages((prev) => prev.map((m) => (m.id === replyId ? { ...m, id: messageId } : m)));
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
      setStreamingId(null);
      setReplying(false);
    }
  };

  const generate = async (kind: 'image' | 'video', prompt: string) => {
    if (!current) return;
    try {
      const res = await api.createGeneration(kind, current.id, prompt || undefined, undefined);
      const taskId = res.task_id;
      const gen: GenerationState = { status: 'pending', kind, task_id: taskId };
      setMessages((prev) => [
        ...prev,
        {
          id: `gen-${taskId}`,
          role: 'assistant',
          content: '',
          feedback: 'none',
          created_at: new Date().toISOString(),
          generation: gen,
        },
      ]);
      const timer = setInterval(async () => {
        const g = await api.getGeneration(taskId);
        const status: GenerationState['status'] =
          g.status === 'success'
            ? 'done'
            : g.status === 'queued' || g.status === 'running'
              ? 'processing'
              : g.status === 'failed' ||
                  g.status === 'safety_blocked' ||
                  g.status === 'cancelled'
                ? 'failed'
                : 'pending';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === `gen-${taskId}`
              ? {
                  ...m,
                  generation: {
                    ...(m.generation as GenerationState),
                    status,
                    url: g.url,
                  },
                }
              : m,
          ),
        );
        if (status === 'done' || status === 'failed') {
          pollTimersRef.current.delete(timer);
          clearInterval(timer);
        }
      }, 1500);
      pollTimersRef.current.add(timer);
    } catch {
      // 忽略生成失败
    }
  };

  if (loading) {
    return (
      <div className="mesh-bg flex min-h-screen flex-col items-center justify-center gap-3">
        <div className="flex gap-1.5">
          <span className="dot-1 h-3 w-3 rounded-full bg-[#a78bfa]" />
          <span className="dot-2 h-3 w-3 rounded-full bg-[#a78bfa]" />
          <span className="dot-3 h-3 w-3 rounded-full bg-[#a78bfa]" />
        </div>
        <span className="text-sm text-foreground/40">{t('common.loading')}</span>
      </div>
    );
  }

  if (!user) return null;

  if (characters.length === 0) {
    return (
      <div className="mesh-bg flex min-h-screen flex-col items-center justify-center gap-4 px-6 pt-16 text-center">
        <Navbar />
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-primary/15 to-accent/10 shadow-inner">
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#a78bfa"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <div className="space-y-1">
          <p className="text-lg font-medium text-foreground/70">{t('chat.noCharacters')}</p>
          <p className="text-sm text-foreground/40">
            {t('chat.createFirstHint') || '创建你的第一个角色，开启陪伴之旅'}
          </p>
        </div>
        <button
          onClick={() => router.push('/create')}
          className="mt-2 rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-6 py-2.5 font-medium text-white shadow-md transition hover:shadow-glow"
        >
          {t('chat.createFirst')}
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      <Navbar />
      <div className="flex-1 overflow-hidden pt-16">
        <ChatLayout
          characterName={current?.name ?? ''}
          characters={characters}
          currentId={current?.id ?? null}
          onSelectCharacter={(id) => {
            const found = characters.find((c) => c.id === id);
            if (found) selectCharacter(found);
          }}
          messages={messages}
          loading={false}
          onSend={(text, attachments) => {
            send(text, attachments);
          }}
          onGenerate={generate}
          sending={replying}
          streamingId={streamingId}
          referenceImages={referenceImages}
          onReferenceImagesChange={setReferenceImages}
        />
      </div>
    </div>
  );
}
