import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  // 支持的语言
  locales: ['en', 'zh', 'ja', 'es'],
  // 默认语言
  defaultLocale: 'en',
  // 默认语言不带前缀，其他语言带前缀（如 /zh/chat）
  localePrefix: 'as-needed',
});

export const localeNames: Record<string, string> = {
  en: 'English',
  zh: '中文',
  ja: '日本語',
  es: 'Español',
};

export type Locale = (typeof routing.locales)[number];
