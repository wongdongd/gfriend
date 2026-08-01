/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // AVATARA 深色主题色板（对齐 Figma 设计稿）
        background: '#0a0b0f',
        foreground: '#f0ede8',
        card: '#13141a',
        'card-foreground': '#e8e4de',
        primary: {
          DEFAULT: '#7c3aed',
          foreground: '#ffffff',
        },
        secondary: {
          DEFAULT: '#1e1f28',
          foreground: '#a09898',
        },
        accent: {
          DEFAULT: '#06b6d4',
          foreground: '#0a0b0f',
        },
        muted: {
          DEFAULT: '#1a1b22',
          foreground: '#6b6880',
        },
        // 保留旧 brand 色，便于渐进迁移
        brand: {
          50: '#fdf6f0',
          100: '#faead9',
          200: '#f4d0ad',
          300: '#edb079',
          400: '#e58a4f',
          500: '#dc6f2e',
          600: '#c95a23',
          700: '#a6461f',
          800: '#873a20',
          900: '#6f311e',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        display: ['Cinzel', 'serif'],
        body: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '0.75rem',
      },
      boxShadow: {
        glow: '0 0 40px rgba(124,58,237,0.4)',
        'glow-lg': '0 0 60px rgba(124,58,237,0.25), 0 40px 80px rgba(0,0,0,0.6)',
      },
    },
  },
  plugins: [],
};
