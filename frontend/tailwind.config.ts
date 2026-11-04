import type { Config } from 'tailwindcss';

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg, #FAFAF7)',
        surface: 'var(--surface, #FFFFFF)',
        ink: {
          DEFAULT: 'var(--ink, #1B1F24)',
          muted: 'var(--ink-muted, #4B5360)',
        },
        primary: {
          DEFAULT: 'var(--primary, #1F5FBF)',
          ink: 'var(--primary-ink, #FFFFFF)',
        },
        success: 'var(--success, #1E7A46)',
        warning: 'var(--warning, #8A5A00)',
        danger: 'var(--danger, #B42318)',
        border: 'var(--border, #D5D9E0)',
      },
      borderRadius: {
        sm: 'var(--radius-sm, 6px)',
        md: 'var(--radius-md, 10px)',
      },
    },
  },
  plugins: [],
} satisfies Config;

