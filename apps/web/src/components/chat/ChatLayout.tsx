'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useTranslations } from 'next-intl';
import Composer from './Composer';
import MessageList from './MessageList';
import ReferencePanel, { type ReferenceImage } from './ReferencePanel';
import type { Message as Msg, Attachment } from '@/types/chat';

interface MiniCharacter {
  id: string;
  name: string;
}

interface ChatLayoutProps {
  characterName: string;
  characterAvatar?: string;
  /** 用户的全部角色列表，用于在侧栏切换 */
  characters?: MiniCharacter[];
  /** 当前角色 ID，用于在侧栏高亮 */
  currentId?: string | null;
  /** 切换到指定角色 */
  onSelectCharacter?: (id: string) => void;
  messages: Msg[];
  loading: boolean;
  onSend: (text: string, attachments: Attachment[]) => void;
  onGenerate: (kind: 'image' | 'video', prompt: string) => void;
  sending: boolean;
  streamingId?: string | null;
  referenceImages: ReferenceImage[];
  onReferenceImagesChange: (
    updater: ReferenceImage[] | ((prev: ReferenceImage[]) => ReferenceImage[]),
  ) => void;
}

function AvatarChar({ name, src }: { name: string; src?: string }) {
  if (src) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={src} alt={name} className="h-full w-full object-cover" />;
  }
  const ch = (name || '?').charAt(0).toUpperCase();
  return (
    <span className="bg-gradient-to-br from-[#a78bfa] to-[#06b6d4] bg-clip-text text-lg font-bold text-transparent">
      {ch}
    </span>
  );
}

export default function ChatLayout({
  characterName,
  characterAvatar,
  characters,
  currentId,
  onSelectCharacter,
  messages,
  loading,
  onSend,
  onGenerate,
  sending,
  streamingId,
  referenceImages,
  onReferenceImagesChange,
}: ChatLayoutProps) {
  const t = useTranslations('chat');
  const [panelOpen, setPanelOpen] = useState(true);
  const [charListOpen, setCharListOpen] = useState(false);
  const [injectAttachment, setInjectAttachment] = useState<Attachment | null>(null);

  const handleInject = (img: ReferenceImage) => {
    if (!img.asset_id) return;
    setInjectAttachment({
      kind: 'image',
      url: img.url,
      asset_id: img.asset_id,
    });
  };

  const handleSelectChar = (id: string) => {
    setCharListOpen(false);
    onSelectCharacter?.(id);
  };

  return (
    <div className="mesh-bg flex h-full">
      {/* 最左侧：角色切换侧栏（可折叠） */}
      <div
        className={`relative z-20 shrink-0 overflow-hidden border-r border-white/[0.06] bg-[#0d0e14]/95 transition-[width] duration-300 ease-out ${
          charListOpen ? 'w-[260px]' : 'w-0'
        }`}
      >
        <div className="flex h-full w-[260px] flex-col">
          <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
            <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-foreground/50">
              {t('myCharacters')}
            </span>
            <button
              onClick={() => setCharListOpen(false)}
              className="flex h-6 w-6 items-center justify-center rounded-md text-foreground/40 transition hover:bg-white/5 hover:text-foreground"
              title={t('backHome') || 'Close'}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto py-2">
            {(characters ?? []).map((c) => {
              const active = c.id === currentId;
              return (
                <button
                  key={c.id}
                  onClick={() => handleSelectChar(c.id)}
                  className={`flex w-full items-center gap-2.5 px-3 py-2.5 text-left transition ${
                    active
                      ? 'bg-primary/15 text-[#a78bfa]'
                      : 'text-foreground/70 hover:bg-white/5 hover:text-foreground'
                  }`}
                >
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    active ? 'bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] text-white' : 'bg-white/10 text-foreground/60'
                  }`}>
                    {(c.name?.[0] ?? '?').toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="m-0 truncate text-[13px] font-medium">{c.name}</p>
                    {active && (
                      <p className="m-0 flex items-center gap-1 text-[10px] text-[#34d399]">
                        <span className="inline-block h-1 w-1 rounded-full bg-[#34d399]" />
                        {t('online')}
                      </p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
          <Link
            href="/characters"
            className="border-t border-white/[0.06] px-4 py-3 text-[11px] font-medium text-foreground/50 transition hover:bg-white/5 hover:text-foreground"
          >
            {t('manageCharacters') || '管理全部角色 →'}
          </Link>
        </div>
      </div>

      {/* 左侧参考图侧栏 */}
      <div
        className={`relative shrink-0 overflow-hidden transition-[width] duration-300 ease-out ${
          panelOpen ? 'w-[300px]' : 'w-0'
        }`}
      >
        <ReferencePanel images={referenceImages} onChange={onReferenceImagesChange} onInject={handleInject} />
      </div>

      {/* 主对话区 */}
      <div className="flex h-full min-w-0 flex-1 flex-col">
        {/* 顶部头栏 */}
        <header className="z-10 border-b border-primary/[0.15] bg-[#0a0b0f]/70 backdrop-blur-xl">
          <div className="flex items-center justify-between px-4 py-2.5">
            <div className="flex items-center gap-3">
              <Link
                href="/"
                className="flex h-9 w-9 items-center justify-center rounded-full text-foreground/40 transition hover:bg-primary/10 hover:text-[#a78bfa]"
                title={t('backHome')}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </Link>

              {/* 切换角色按钮：展开/收起最左侧的角色列表 */}
              {(characters?.length ?? 0) > 0 && (
                <button
                  type="button"
                  onClick={() => setCharListOpen((v) => !v)}
                  className={`flex h-9 w-9 items-center justify-center rounded-full transition ${
                    charListOpen
                      ? 'bg-primary/15 text-[#a78bfa]'
                      : 'text-foreground/40 hover:bg-primary/10 hover:text-[#a78bfa]'
                  }`}
                  title={t('myCharacters')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                </button>
              )}

              {/* 角色头像 + 在线点 */}
              <div className="relative">
                <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-primary/10 ring-2 ring-[#0a0b0f] shadow-sm">
                  <AvatarChar name={characterName} src={characterAvatar} />
                </div>
                <span className="pulse-ring absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#0a0b0f] bg-[#34d399]" />
              </div>

              <div className="leading-tight">
                <h1 className="text-[15px] font-semibold text-foreground">{characterName}</h1>
                <p className="flex items-center gap-1 text-[11px] text-[#34d399]">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#34d399]" />
                  {t('online') || 'Online'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setPanelOpen((v) => !v)}
                className={`flex h-9 items-center gap-1.5 rounded-full border px-3 text-xs font-medium transition ${
                  panelOpen
                    ? 'border-primary/30 bg-primary/10 text-[#a78bfa]'
                    : 'border-white/10 bg-white/5 text-foreground/60 hover:border-primary/30 hover:bg-primary/10 hover:text-[#a78bfa]'
                }`}
                title={panelOpen ? '收起参考图' : '展开参考图'}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <path d="M21 15l-5-5L5 21" />
                </svg>
                {t('reference') || '参考图'}
                {referenceImages.length > 0 && (
                  <span className="ml-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-white">
                    {referenceImages.length}
                  </span>
                )}
              </button>

              <Link
                href="/"
                className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-medium text-foreground/60 transition hover:border-primary/30 hover:bg-primary/10 hover:text-[#a78bfa]"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 5v14M5 12h14" />
                </svg>
                {t('newChat')}
              </Link>
            </div>
          </div>
        </header>

        {/* 消息列表 */}
        <MessageList messages={messages} characterName={characterName} loading={loading} streamingId={streamingId} />

        {/* 输入区 */}
        <Composer
          onSend={onSend}
          onGenerate={onGenerate}
          disabled={sending}
          characterName={characterName}
          injectAttachment={injectAttachment}
          onInjected={() => setInjectAttachment(null)}
        />
      </div>
    </div>
  );
}
