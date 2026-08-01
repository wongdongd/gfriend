'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import type { Attachment } from '@/types/chat';

interface ImageMessageProps {
  attachment: Attachment;
  compact?: boolean;
}

export default function ImageMessage({ attachment, compact }: ImageMessageProps) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`overflow-hidden rounded-xl border border-white/10 shadow-sm transition hover:border-primary/40 hover:opacity-90 ${
          compact ? 'h-24 w-24' : 'h-40 w-40'
        }`}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={attachment.url} alt="attachment" className="h-full w-full object-cover" />
      </button>
      <Modal open={open} onClose={() => setOpen(false)}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={attachment.url}
          alt="attachment"
          className="max-h-[80vh] w-full rounded-2xl object-contain"
        />
      </Modal>
    </>
  );
}
