'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useTranslations } from 'next-intl';
import Composer from './Composer';
import MessageList from './MessageList';
import ReferencePanel, { type ReferenceImage } from './ReferencePanel';
import type { Message as Msg, Attachment } from '@/types/chat';

interface ChatLayoutProps {
  characterName: string;
  characterAvatar?: string;
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
  const [injectAttachment, setInjectAttachment] = useState<Attachment | null>(null);

  const handleInject = (img: ReferenceImage) => {
    if (!img.asset_id) return;
    setInjectAttachment({
      kind: 'image',
      url: img.url,
      asset_id: img.asset_id,
    });
  };

  return (
    <div className="mesh-bg flex h-full">
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
