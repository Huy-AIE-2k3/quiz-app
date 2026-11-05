import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--bg-canvas)',
        surface: 'var(--bg-surface)',
        elevated: 'var(--bg-elevated)',
        'subtle-accent': 'var(--bg-subtle-accent)',

        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',

        'line-subtle': 'var(--border-subtle)',
        'line-strong': 'var(--border-strong)',
        'line-accent': 'var(--border-accent)',

        brand: {
          DEFAULT: 'var(--brand-primary)',
          hover: 'var(--brand-hover)',
          glow: 'var(--brand-glow)',
        },

        status: {
          correct: {
            bg: 'var(--status-correct-bg)',
            border: 'var(--status-correct-border)',
            text: 'var(--status-correct-text)',
          },
          wrong: {
            bg: 'var(--status-wrong-bg)',
            border: 'var(--status-wrong-border)',
            text: 'var(--status-wrong-text)',
          },
          flag: {
            bg: 'var(--status-flag-bg)',
            border: 'var(--status-flag-border)',
            text: 'var(--status-flag-text)',
          },
        },

        timer: {
          normal: {
            text: 'var(--timer-normal-text)',
            border: 'var(--timer-normal-border)',
            bg: 'var(--timer-normal-bg)',
            dot: 'var(--timer-normal-dot)',
          },
          warning: {
            text: 'var(--timer-warning-text)',
            border: 'var(--timer-warning-border)',
            bg: 'var(--timer-warning-bg)',
            dot: 'var(--timer-warning-dot)',
          },
          critical: {
            text: 'var(--timer-critical-text)',
            border: 'var(--timer-critical-border)',
            bg: 'var(--timer-critical-bg)',
            dot: 'var(--timer-critical-dot)',
          },
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        display: ['var(--font-display)'],
        mono: ['var(--font-mono)'],
        math: ['var(--font-math)'],
      },
      borderRadius: {
        xs: 'var(--radius-xs)',
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
    },
  },
  plugins: [],
} satisfies Config;
