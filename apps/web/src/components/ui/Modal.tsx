'use client';

import { useEffect, ReactNode } from 'react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
}

export default function Modal({ open, onClose, children, title }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] max-w-3xl overflow-auto rounded-2xl border border-white/[0.08] bg-[#13141a] shadow-glow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className="border-b border-white/[0.08] px-5 py-3 text-lg font-semibold text-foreground">
            {title}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
