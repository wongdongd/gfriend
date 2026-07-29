import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth-context';

export const metadata: Metadata = {
  title: '陪伴 · AI 人物陪伴平台',
  description: '让用户亲手创作、培养并与之长期相处的 AI 人物陪伴产品',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={process.env.NODE_ENV === 'development' ? '' : ''}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
