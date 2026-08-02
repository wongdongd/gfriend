'use client';

import { useTranslations } from 'next-intl';
import { Link, useRouter, usePathname } from '@/i18n/navigation';
import { useAuth } from '@/lib/auth-context';
import LanguageSwitcher from '@/components/language-switcher';

/**
 * 顶部导航栏
 * 深色玻璃拟态、紫青渐变 Logo、固定定位
 */
export default function Navbar() {
  const { user, loading, logout } = useAuth();
  const t = useTranslations();
  const router = useRouter();
  const pathname = usePathname();

  // 高亮当前路由
  const isActive = (href: string) => {
    const clean = pathname.replace(/^\/(en|zh|ja|es)/, '') || '/';
    return clean === href || (href !== '/' && clean.startsWith(href));
  };

  const navLinkClass = (href: string) =>
    `rounded-md px-3.5 py-1.5 text-sm font-medium transition ${
      isActive(href)
        ? 'bg-primary/15 text-[#a78bfa]'
        : 'text-foreground/60 hover:bg-white/5 hover:text-foreground'
    }`;

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <nav
      className="fixed inset-x-0 top-0 z-[100] border-b border-white/[0.06] bg-[#0a0b0f]/85 backdrop-blur-xl"
      style={{ height: 64 }}
    >
      <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#06b6d4] text-base">
            ✦
          </div>
          <span className="font-display text-lg font-bold tracking-[0.05em] text-foreground">
            {t('nav.brand')}
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden items-center gap-1 md:flex">
          {user ? (
            <>
              <Link href="/characters" className={navLinkClass('/characters')}>
                {t('nav.myCharacters')}
              </Link>
              <Link href="/chat" className={navLinkClass('/chat')}>
                {t('nav.chat')}
              </Link>
              <Link href="/create" className={navLinkClass('/create')}>
                {t('nav.createCompanion')}
              </Link>
              <Link href="/billing" className={navLinkClass('/billing')}>
                {t('nav.pricing')}
              </Link>
            </>
          ) : (
            <>
              <Link href="/" className={navLinkClass('/')}>
                {t('nav.features')}
              </Link>
              <Link href="/billing" className={navLinkClass('/billing')}>
                {t('nav.pricing')}
              </Link>
            </>
          )}
        </div>

        {/* Auth area */}
        <div className="flex items-center gap-3">
          <LanguageSwitcher />

          {loading ? null : user ? (
            <>
              <div className="flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/10 px-3 py-1.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-[#7c3aed] to-[#06b6d4] text-xs font-bold text-white">
                  {(user.email?.[0] ?? 'A').toUpperCase()}
                </div>
                <span className="text-[13px] font-medium text-[#a78bfa]">
                  {user.email?.split('@')[0] ?? 'Aether_7'}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="rounded-md border border-white/[0.12] px-3.5 py-1.5 text-[13px] text-foreground/50 transition hover:border-red-400/40 hover:text-red-400"
              >
                {t('nav.signOut')}
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-md px-3.5 py-1.5 text-sm text-foreground/60 transition hover:text-foreground"
              >
                {t('nav.login')}
              </Link>
              <Link
                href="/login?mode=register"
                className="rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] px-5 py-2 text-sm font-semibold text-white transition hover:opacity-85"
              >
                {t('nav.getStarted')}
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
