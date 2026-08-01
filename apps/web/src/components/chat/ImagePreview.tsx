'use client';

import type { Attachment } from '@/types/chat';

interface ImagePreviewProps {
  attachments: Attachment[];
  onRemove: (index: number) => void;
}

export default function ImagePreview({ attachments, onRemove }: ImagePreviewProps) {
  if (attachments.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2 pb-2">
      {attachments.map((a, i) => (
        <div key={a.asset_id ?? i} className="group relative">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={a.url}
            alt="preview"
            className="h-16 w-16 rounded-xl border border-white/10 object-cover shadow-sm"
          />
          {a.asset_id ? null : (
            <span className="spin absolute inset-0 m-auto h-4 w-4 rounded-full border-2 border-white/30 border-t-white" />
          )}
          <button
            type="button"
            onClick={() => onRemove(i)}
            className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-[#7c3aed] text-xs text-white shadow transition hover:bg-[#5b21b6]"
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
        </div>
      ))}
    </div>
  );
}
