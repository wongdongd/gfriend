import { createNavigation } from 'next-intl/navigation';
import { routing } from './routing';

// 基于路由配置的导航工具：Link / redirect / usePathname / useRouter / getPathname
export const { Link, redirect, usePathname, useRouter, getPathname } = createNavigation(routing);
