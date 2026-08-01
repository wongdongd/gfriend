'use client';

import type { Message } from '@/types/chat';

interface MessageBubbleProps {
  message: Message;
  characterName: string;
  isStreaming?: boolean;
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function AvatarChar({ name }: { name: string }) {
  const ch = (name || '?').charAt(0).toUpperCase();
  return (
    <span className="bg-gradient-to-br from-[#a78bfa] to-[#06b6d4] bg-clip-text text-sm font-bold text-transparent">
      {ch}
    </span>
  );
}

export default function MessageBubble({ message, characterName, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const time = formatTime(message.created_at);

  return (
    <div className={`flex w-full animate-msg-in items-end gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* 头像 */}
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full shadow-sm ${
          isUser
            ? 'bg-gradient-to-br from-white/15 to-white/5'
            : 'bg-primary/10 ring-1 ring-primary/20'
        }`}
      >
        {isUser ? (
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#a78bfa"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : (
          <AvatarChar name={characterName} />
        )}
      </div>

      {/* 气泡 + 时间 */}
      <div className={`flex max-w-[75%] flex-col gap-0.5 ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`whitespace-pre-wrap break-words px-4 py-2.5 text-[15px] leading-relaxed shadow-sm ${
            isUser
              ? 'rounded-2xl rounded-br-md bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] text-white'
              : 'rounded-2xl rounded-bl-md border border-white/[0.08] bg-card text-foreground'
          }`}
        >
          <span className={isStreaming ? 'typing-cursor' : ''}>{message.content}</span>
        </div>
        <span className="px-1 text-[10px] text-foreground/30">{time}</span>
      </div>
    </div>
  );
}
