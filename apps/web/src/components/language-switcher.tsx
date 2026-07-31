'use client';

import { useState } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { usePathname, useRouter } from '@/i18n/navigation';
import { routing, localeNames } from '@/i18n/routing';

export default function LanguageSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 rounded-full border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:border-brand-400 hover:text-brand-700 transition"
        aria-label="Switch language"
      >
        <span>🌐</span>
        <span>{localeNames[locale]}</span>
        <span className="text-xs opacity-60">▾</span>
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-36 rounded-xl border border-gray-100 bg-white py-1 shadow-lg">
          {routing.locales.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => {
                setOpen(false);
                router.replace(pathname, { locale: l });
              }}
              className={`block w-full px-4 py-2 text-left text-sm hover:bg-gray-50 transition ${
                l === locale ? 'font-semibold text-brand-700' : 'text-gray-700'
              }`}
            >
              {localeNames[l]}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
