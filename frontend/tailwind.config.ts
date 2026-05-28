import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // SiteTrack — dark slate + indigo accent
        navy: {
          950: '#080d16',
          900: '#0d1424',
          800: '#111d32',
          700: '#162440',
          600: '#1c2f52',
          500: '#243b66',
          400: '#2d4a7a',
        },
        steel: {
          600: '#3730a3',
          500: '#4338ca',
          400: '#6366f1',   // PRIMARY accent — indigo
          300: '#818cf8',
          200: '#a5b4fc',
          100: '#c7d2fe',
          50:  '#e0e7ff',
        },
        // Semantic
        critical: '#dc2626',
        warning:  '#d97706',
        info:     '#3b82f6',
        success:  '#16a34a',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config
