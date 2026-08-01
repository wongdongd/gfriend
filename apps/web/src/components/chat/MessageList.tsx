'use client';

import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import ImageMessage from './ImageMessage';
import GenerationCard from './GenerationCard';
import type { Message as Msg } from '@/types/chat';

interface MessageListProps {
  messages: Msg[];
  characterName: string;
  loading: boolean;
  streamingId?: string | null;
}

export default function MessageList({ messages, characterName, loading, streamingId }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (loading && messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3">
        <div className="flex gap-1.5">
          <span className="dot-1 h-2.5 w-2.5 rounded-full bg-[#a78bfa]" />
          <span className="dot-2 h-2.5 w-2.5 rounded-full bg-[#a78bfa]" />
          <span className="dot-3 h-2.5 w-2.5 rounded-full bg-[#a78bfa]" />
        </div>
        <span className="text-sm text-foreground/40">Loading…</span>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
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
          <p className="text-lg font-medium text-foreground/70">
            Start chatting with {characterName}
          </p>
          <p className="text-sm text-foreground/40">
            Send a message, attach an image, or generate images/videos
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 overflow-y-auto px-4 py-6">
      {messages.map((m) => {
        if (m.generation) {
          return (
            <div key={m.id} className="flex flex-row items-end gap-2">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 ring-1 ring-primary/20">
                <span className="bg-gradient-to-br from-[#a78bfa] to-[#06b6d4] bg-clip-text text-sm font-bold text-transparent">
                  {(characterName || '?').charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="max-w-[75%]">
                <GenerationCard generation={m.generation} />
              </div>
            </div>
          );
        }
        if (m.attachments && m.attachments.length > 0) {
          return (
            <div
              key={m.id}
              className={`flex flex-col gap-1.5 ${m.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className={`flex gap-1.5 ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'} items-end`}>
                {m.attachments.map((a, i) => (
                  <ImageMessage key={a.asset_id ?? i} attachment={a} compact />
                ))}
              </div>
              {m.content && (
                <MessageBubble message={m} characterName={characterName} isStreaming={streamingId === m.id} />
              )}
            </div>
          );
        }
        return (
          <MessageBubble
            key={m.id}
            message={m}
            characterName={characterName}
            isStreaming={streamingId === m.id}
          />
        );
      })}
      <div ref={endRef} />
    </div>
  );
}
