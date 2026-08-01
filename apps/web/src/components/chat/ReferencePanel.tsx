'use client';

import { useRef } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

export interface ReferenceImage {
  id: string;
  asset_id?: string;
  url: string;
  uploading?: boolean;
}

interface ReferencePanelProps {
  images: ReferenceImage[];
  onChange: (updater: ReferenceImage[] | ((prev: ReferenceImage[]) => ReferenceImage[])) => void;
  onInject: (image: ReferenceImage) => void;
}

function uid() {
  return `ref-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function ReferencePanel({ images, onChange, onInject }: ReferencePanelProps) {
  const t = useTranslations('chat');
  const fileRef = useRef<HTMLInputElement>(null);

  const upload = async (file: File) => {
    if (!file.type.startsWith('image/')) return;
    const placeholder: ReferenceImage = {
      id: uid(),
      url: URL.createObjectURL(file),
      uploading: true,
    };
    onChange((prev) => [placeholder, ...prev]);

    try {
      const { asset_id, url } = await api.uploadImage(file, 'image');
      onChange((prev) =>
        prev.map((img) => (img.id === placeholder.id ? { ...img, asset_id, url, uploading: false } : img)),
      );
    } catch {
      onChange((prev) => prev.filter((img) => img.id !== placeholder.id));
    }
  };

  const onPick = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach(upload);
  };

  const remove = (id: string) => onChange((prev) => prev.filter((i) => i.id !== id));

  return (
    <aside className="flex h-full w-full flex-col border-r border-white/[0.06] bg-[#13141a]/60 backdrop-blur-xl">
      {/* 标题 */}
      <div className="border-b border-white/[0.06] px-4 pb-3 pt-4">
        <h2 className="m-0 text-sm font-semibold text-foreground">
          {t('referenceImages') || 'Reference Images'}
        </h2>
        <p className="mt-0.5 text-[11px] text-foreground/40">
          {t('referenceHint') || 'Upload reference images, click to send to character'}
        </p>
      </div>

      {/* 上传按钮 */}
      <div className="px-4 py-3">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="group flex w-full flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-primary/30 bg-primary/[0.05] px-4 py-5 text-[#a78bfa] transition hover:border-primary/50 hover:bg-primary/[0.1]"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#0a0b0f] shadow-sm ring-1 ring-primary/20 transition group-hover:scale-105">
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
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </div>
          <span className="text-xs font-medium">{t('addReference') || 'Add Reference Image'}</span>
          <span className="text-[10px] text-foreground/40">
            {t('addReferenceSub') || 'Click to upload local image'}
          </span>
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => {
            onPick(e.target.files);
            e.target.value = '';
          }}
        />
      </div>

      {/* 历史网格 */}
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-medium text-foreground/50">
            {t('historyCreations') || 'History'}
          </span>
          <span className="font-mono text-[10px] text-foreground/30">{images.length}</span>
        </div>

        {images.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.02] px-4 py-8 text-center">
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="rgba(160,152,152,0.3)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
            <p className="mt-2 text-[11px] text-foreground/30">
              {t('noReferences') || 'No reference images yet'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {images.map((img) => (
              <div
                key={img.id}
                className="group relative aspect-square overflow-hidden rounded-xl border border-white/[0.08] bg-card shadow-sm transition hover:shadow-md"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={img.url} alt="reference" className="h-full w-full object-cover" />

                {img.uploading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                    <span className="spin h-5 w-5 rounded-full border-2 border-white/30 border-t-white" />
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => remove(img.id)}
                  className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-[#7c3aed] text-xs text-white opacity-0 transition group-hover:opacity-100 hover:bg-[#5b21b6]"
                  title="Delete"
                >
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>

                {!img.uploading && (
                  <button
                    type="button"
                    onClick={() => onInject(img)}
                    className="absolute inset-x-1 bottom-1 flex items-center justify-center gap-1 rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-2 py-1 text-[11px] font-medium text-white opacity-0 shadow-sm transition group-hover:opacity-100"
                    title="Send to chat"
                  >
                    <svg
                      width="11"
                      height="11"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                    {t('inject') || 'Send'}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
