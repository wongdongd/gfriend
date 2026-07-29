/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // 品牌色：温暖陪伴感
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
      },
    },
  },
  plugins: [],
};
