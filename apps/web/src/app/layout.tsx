import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Companion · AI Character Companion',
  description:
    'Create, raise and bond with AI characters you design yourself — a long-term companionship product.',
};

// 根布局只负责全局样式与 metadata，html/body 由 [locale]/layout 输出（lang 随语言动态变化）
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return children;
}
