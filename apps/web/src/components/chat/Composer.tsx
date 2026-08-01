'use client';

import { useState, useRef, KeyboardEvent, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import ImagePreview from './ImagePreview';
import { api } from '@/lib/api';
import type { Attachment } from '@/types/chat';

interface ComposerProps {
  onSend: (text: string, attachments: Attachment[]) => void;
  onGenerate: (kind: 'image' | 'video', prompt: string) => void;
  disabled?: boolean;
  characterName?: string;
  injectAttachment?: Attachment | null;
  onInjected?: () => void;
}

export default function Composer({
  onSend,
  onGenerate,
  disabled,
  characterName,
  injectAttachment,
  onInjected,
}: ComposerProps) {
  const t = useTranslations('chat');
  const [text, setText] = useState('');
  const [pending, setPending] = useState<Attachment[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  // textarea 自适应高度
  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
  }, [text]);

  // 外部注入附件
  useEffect(() => {
    if (!injectAttachment) return;
    setPending((prev) => {
      if (
        prev.some(
          (p) => p.asset_id && injectAttachment.asset_id && p.asset_id === injectAttachment.asset_id,
        )
      ) {
        return prev;
      }
      return [...prev, injectAttachment];
    });
    onInjected?.();
  }, [injectAttachment, onInjected]);

  const send = () => {
    if (disabled || (!text.trim() && pending.length === 0)) return;
    const ready = pending.filter((a) => a.asset_id);
    const uploading = pending.length - ready.length;
    if (uploading > 0) return;
    onSend(text.trim(), ready);
    setText('');
    setPending([]);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const pickFiles = async (files: FileList | null) => {
    if (!files) return;
    const imgs = Array.from(files).filter((f) => f.type.startsWith('image/'));
    if (imgs.length === 0) return;

    const placeholders: Attachment[] = imgs.map((f) => ({
      kind: 'image',
      url: URL.createObjectURL(f),
      asset_id: undefined,
    }));
    setPending((prev) => [...prev, ...placeholders]);

    imgs.forEach(async (file, idx) => {
      try {
        const { asset_id, url } = await api.uploadImage(file, 'image');
        setPending((prev) =>
          prev.map((a, i) => {
            const targetIdx = prev.length - placeholders.length + idx;
            return i === targetIdx ? { ...a, asset_id, url } : a;
          }),
        );
      } catch {
        setPending((prev) => prev.filter((_, i) => i !== prev.length - placeholders.length + idx));
      }
    });
  };

  const canSend = !disabled && (text.trim().length > 0 || pending.length > 0);

  return (
    <div className="border-t border-white/[0.06] bg-[#0a0b0f]/70 backdrop-blur-xl">
      <div className="mx-auto w-full max-w-3xl px-4 py-3">
        {/* 附件预览 */}
        <ImagePreview attachments={pending} onRemove={(i) => setPending(pending.filter((_, idx) => idx !== i))} />

        {/* 主输入行 */}
        <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-[#13141a] px-2 py-2 shadow-sm transition focus-within:border-primary/40 focus-within:shadow-md">
          {/* 附件按钮 */}
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-foreground/40 transition hover:bg-primary/10 hover:text-[#a78bfa]"
            title={t('attachImage')}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={(e) => {
              pickFiles(e.target.files);
              e.target.value = '';
            }}
          />

          {/* 文本框 */}
          <textarea
            ref={taRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder={t('inputPlaceholder', { name: characterName || '' })}
            className="max-h-[140px] flex-1 resize-none bg-transparent py-1.5 text-[15px] leading-relaxed text-foreground outline-none placeholder:text-foreground/30"
          />

          {/* 生成按钮组 */}
          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              onClick={() => onGenerate('image', text)}
              disabled={disabled}
              className="flex h-9 w-9 items-center justify-center rounded-xl text-foreground/40 transition hover:bg-primary/10 hover:text-[#a78bfa] disabled:opacity-40"
              title={t('genImage')}
            >
              <svg
                width="18"
                height="18"
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
            </button>
            <button
              type="button"
              onClick={() => onGenerate('video', text)}
              disabled={disabled}
              className="flex h-9 w-9 items-center justify-center rounded-xl text-foreground/40 transition hover:bg-accent/10 hover:text-[#06b6d4] disabled:opacity-40"
              title={t('genVideo')}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polygon points="23 7 16 12 23 17 23 7" />
                <rect x="1" y="5" width="15" height="14" rx="2" />
              </svg>
            </button>
          </div>

          {/* 发送按钮 */}
          <button
            type="button"
            onClick={send}
            disabled={!canSend}
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition ${
              canSend
                ? 'bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] text-white shadow-sm hover:shadow-md'
                : 'bg-white/5 text-foreground/20'
            }`}
            title={t('send')}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        {/* 提示行 */}
        <p className="mt-1.5 px-2 text-[11px] text-foreground/30">
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  );
}
