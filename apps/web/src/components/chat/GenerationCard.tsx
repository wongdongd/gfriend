'use client';

import type { GenerationState } from '@/types/chat';

interface GenerationCardProps {
  generation: GenerationState;
}

export default function GenerationCard({ generation }: GenerationCardProps) {
  const { status, kind, url, progress } = generation;
  const label = kind === 'video' ? 'Video' : 'Image';

  if (status === 'pending' || status === 'processing') {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-primary/30 bg-primary/[0.08] px-4 py-3">
        <div className="flex gap-1">
          <span className="dot-1 h-2 w-2 rounded-full bg-[#a78bfa]" />
          <span className="dot-2 h-2 w-2 rounded-full bg-[#a78bfa]" />
          <span className="dot-3 h-2 w-2 rounded-full bg-[#a78bfa]" />
        </div>
        <div className="text-sm text-foreground/70">
          Generating {label}
          {typeof progress === 'number' && progress > 0 && (
            <span className="ml-1 font-mono text-xs text-[#a78bfa]">
              · {Math.round(progress * 100)}%
            </span>
          )}
        </div>
      </div>
    );
  }

  if (status === 'done' && url) {
    return (
      <div className="overflow-hidden rounded-2xl border border-primary/20 bg-card shadow-sm">
        <div className="flex items-center gap-1.5 px-3 py-1.5 font-mono text-xs text-[#a78bfa]">
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {kind === 'video' ? (
              <>
                <polygon points="23 7 16 12 23 17 23 7" />
                <rect x="1" y="5" width="15" height="14" rx="2" />
              </>
            ) : (
              <>
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </>
            )}
          </svg>
          {label} generated
        </div>
        {kind === 'video' ? (
          <video src={url} controls className="max-h-64 w-full bg-black" />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={url} alt="generation" className="max-h-64 w-full object-cover" />
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 rounded-2xl border border-red-500/30 bg-red-500/[0.08] px-4 py-3 text-sm text-red-400">
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="15" y1="9" x2="9" y2="15" />
        <line x1="9" y1="9" x2="15" y2="15" />
      </svg>
      {label} generation failed. Please try again.
    </div>
  );
}
