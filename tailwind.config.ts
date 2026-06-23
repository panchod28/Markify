import type { Config } from 'tailwindcss';

const config: Config = {
  // Importante: aplicar dark mode mediante atributo [data-theme="dark"] en <html>
  // NO usar la clase 'dark' de Tailwind — usamos CSS custom properties.
  darkMode: ['attribute', '[data-theme="dark"]'],

  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],

  theme: {
    extend: {
      // Mapear CSS custom properties a clases Tailwind
      colors: {
        accent: {
          DEFAULT:  'var(--color-accent)',
          hover:    'var(--color-accent-hover)',
          active:   'var(--color-accent-active)',
          subtle:   'var(--color-accent-subtle)',
        },
        success:  {
          DEFAULT: 'var(--color-success)',
          subtle:  'var(--color-success-subtle)',
        },
        error:    {
          DEFAULT: 'var(--color-error)',
          subtle:  'var(--color-error-subtle)',
        },
        warning:  {
          DEFAULT: 'var(--color-warning)',
          subtle:  'var(--color-warning-subtle)',
        },
        bg:       'var(--color-background)',
        surface:  {
          DEFAULT:   'var(--color-surface)',
          secondary: 'var(--color-surface-secondary)',
          elevated:  'var(--color-surface-elevated)',
        },
        text: {
          primary:   'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          tertiary:  'var(--color-text-tertiary)',
          disabled:  'var(--color-text-disabled)',
          onaccent:  'var(--color-text-on-accent)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          strong:  'var(--color-border-strong)',
          focus:   'var(--color-border-focus)',
        },
      },

      fontFamily: {
        sans: ['var(--font-family)'],
        mono: ['var(--font-family-mono)'],
      },

      fontSize: {
        'xs':   ['var(--text-xs)',   { lineHeight: 'var(--leading-normal)' }],
        'sm':   ['var(--text-sm)',   { lineHeight: 'var(--leading-normal)' }],
        'base': ['var(--text-base)', { lineHeight: 'var(--leading-relaxed)' }],
        'lg':   ['var(--text-lg)',   { lineHeight: 'var(--leading-normal)' }],
        'xl':   ['var(--text-xl)',   { lineHeight: 'var(--leading-tight)' }],
        '2xl':  ['var(--text-2xl)', { lineHeight: 'var(--leading-tight)' }],
        '3xl':  ['var(--text-3xl)', { lineHeight: 'var(--leading-tight)' }],
      },

      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },

      boxShadow: {
        sm:    'var(--shadow-sm)',
        md:    'var(--shadow-md)',
        lg:    'var(--shadow-lg)',
        modal: 'var(--shadow-modal)',
      },

      transitionDuration: {
        fast: 'var(--duration-fast)',
        base: 'var(--duration-base)',
        slow: 'var(--duration-slow)',
      },

      transitionTimingFunction: {
        default: 'var(--ease-default)',
        spring:  'var(--ease-spring)',
      },
    },
  },

  plugins: [],
};

export default config;
