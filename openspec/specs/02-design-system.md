# Spec 02 — Design System
> Markify — Tokens visuales, CSS custom properties, Tailwind config, tipografía, iconos y animaciones.
> Archivos destino: `src/index.css`, `tailwind.config.ts`, `src/lib/cn.ts`

---

## 1. Principios de diseño

- **Apple-quality:** Limpio, espacioso, jerarquía visual clara. Referentes: macOS Ventura UI, Linear.app, Vercel Dashboard.
- **Consistencia:** Todos los valores se definen como CSS custom properties. Nunca hardcodear colores o tamaños en componentes.
- **Adaptabilidad:** Light y dark mode nativo. Todas las variables tienen ambas variantes.
- **Accesibilidad:** Contraste mínimo WCAG AA en texto sobre fondo. Respetar `prefers-reduced-motion`.
- **Sistema de 8px:** Todo el espaciado es múltiplo de 4px, preferiblemente de 8px.

---

## 2. CSS Custom Properties (`src/index.css`)

```css
/* ========================================================================
   MARKIFY — DESIGN TOKENS
   Importar en src/main.tsx antes de cualquier otro CSS.
   ======================================================================== */

@tailwind base;
@tailwind components;
@tailwind utilities;

/* ── Base reset ─────────────────────────────────────────────────────────── */
*, *::before, *::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: var(--font-family);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
  background-color: var(--color-background);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Light mode (default) ───────────────────────────────────────────────── */
:root {
  /* ── Colores de acento ── */
  --color-accent:           #007AFF;   /* Apple Blue */
  --color-accent-hover:     #0066D6;
  --color-accent-active:    #0055B3;
  --color-accent-subtle:    rgba(0, 122, 255, 0.10);
  --color-accent-subtle-hover: rgba(0, 122, 255, 0.16);

  /* ── Semánticos ── */
  --color-success:          #34C759;
  --color-success-subtle:   rgba(52, 199, 89, 0.12);
  --color-error:            #FF3B30;
  --color-error-subtle:     rgba(255, 59, 48, 0.12);
  --color-warning:          #FF9500;
  --color-warning-subtle:   rgba(255, 149, 0, 0.12);

  /* ── Superficies ── */
  --color-background:       #F2F2F7;  /* systemGroupedBackground */
  --color-surface:          #FFFFFF;  /* systemBackground */
  --color-surface-secondary:#F2F2F7;  /* secondarySystemBackground */
  --color-surface-elevated: #FFFFFF;  /* elevatedSystemBackground */

  /* ── Texto ── */
  --color-text-primary:     #000000;
  --color-text-secondary:   #636366;
  --color-text-tertiary:    #AEAEB2;
  --color-text-disabled:    #C7C7CC;
  --color-text-on-accent:   #FFFFFF;  /* texto sobre botones accent */

  /* ── Bordes ── */
  --color-border:           rgba(60, 60, 67, 0.12);
  --color-border-strong:    rgba(60, 60, 67, 0.29);
  --color-border-focus:     #007AFF;  /* borde de focus / active */

  /* ── Drop zone ── */
  --color-dropzone-bg:           rgba(0, 122, 255, 0.03);
  --color-dropzone-border:       rgba(0, 122, 255, 0.30);
  --color-dropzone-bg-active:    rgba(0, 122, 255, 0.08);
  --color-dropzone-border-active:#007AFF;

  /* ── Overlay (modales) ── */
  --color-overlay:          rgba(0, 0, 0, 0.40);

  /* ── Scrollbar ── */
  --color-scrollbar-thumb:  rgba(0, 0, 0, 0.20);
  --color-scrollbar-track:  transparent;
}

/* ── Dark mode ──────────────────────────────────────────────────────────── */
[data-theme="dark"] {
  --color-accent:           #0A84FF;
  --color-accent-hover:     #409CFF;
  --color-accent-active:    #6DB9FF;
  --color-accent-subtle:    rgba(10, 132, 255, 0.16);
  --color-accent-subtle-hover: rgba(10, 132, 255, 0.24);

  --color-success:          #30D158;
  --color-success-subtle:   rgba(48, 209, 88, 0.16);
  --color-error:            #FF453A;
  --color-error-subtle:     rgba(255, 69, 58, 0.16);
  --color-warning:          #FF9F0A;
  --color-warning-subtle:   rgba(255, 159, 10, 0.16);

  --color-background:       #000000;
  --color-surface:          #1C1C1E;
  --color-surface-secondary:#2C2C2E;
  --color-surface-elevated: #3A3A3C;

  --color-text-primary:     #FFFFFF;
  --color-text-secondary:   rgba(235, 235, 245, 0.60);
  --color-text-tertiary:    rgba(235, 235, 245, 0.30);
  --color-text-disabled:    rgba(235, 235, 245, 0.18);
  --color-text-on-accent:   #FFFFFF;

  --color-border:           rgba(255, 255, 255, 0.10);
  --color-border-strong:    rgba(255, 255, 255, 0.20);
  --color-border-focus:     #0A84FF;

  --color-dropzone-bg:           rgba(10, 132, 255, 0.05);
  --color-dropzone-border:       rgba(10, 132, 255, 0.35);
  --color-dropzone-bg-active:    rgba(10, 132, 255, 0.12);
  --color-dropzone-border-active:#0A84FF;

  --color-overlay:          rgba(0, 0, 0, 0.60);

  --color-scrollbar-thumb:  rgba(255, 255, 255, 0.20);
  --color-scrollbar-track:  transparent;
}

/* ── Tipografía ─────────────────────────────────────────────────────────── */
:root {
  /* Sistema de fuentes del OS — Apple SF Pro en Mac, Segoe UI en Windows,
     Ubuntu/Noto en Linux. No cargar Google Fonts. */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Ubuntu',
                 'Helvetica Neue', Arial, sans-serif;
  --font-family-mono: 'SF Mono', 'Cascadia Code', 'Fira Code',
                      'Consolas', 'Courier New', monospace;

  /* Tamaños (escala de Apple HIG) */
  --text-xs:   0.6875rem;  /* 11px — captions muy pequeñas */
  --text-sm:   0.8125rem;  /* 13px — metadata, nombres secundarios */
  --text-base: 0.9375rem;  /* 15px — texto de cuerpo principal */
  --text-lg:   1.0625rem;  /* 17px — texto destacado */
  --text-xl:   1.25rem;    /* 20px — títulos de sección pequeños */
  --text-2xl:  1.5rem;     /* 24px — títulos de sección */
  --text-3xl:  2.125rem;   /* 34px — título principal (dropzone) */

  /* Pesos */
  --font-regular:  400;
  --font-medium:   500;
  --font-semibold: 600;
  --font-bold:     700;

  /* Line heights */
  --leading-tight:   1.2;
  --leading-normal:  1.4;
  --leading-relaxed: 1.6;
}

/* ── Espaciado (grilla de 8px) ──────────────────────────────────────────── */
:root {
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}

/* ── Border radius ──────────────────────────────────────────────────────── */
:root {
  --radius-sm: 6px;   /* chips, badges, tags, progress bars */
  --radius-md: 10px;  /* botones, inputs, file items, tooltips */
  --radius-lg: 14px;  /* cards, paneles, drop zone, sidebars */
  --radius-xl: 20px;  /* modales, superficies grandes */
}

/* ── Sombras ────────────────────────────────────────────────────────────── */
:root {
  --shadow-sm:    0 1px 2px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.04);
  --shadow-md:    0 4px 8px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg:    0 8px 24px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04);
  --shadow-modal: 0 20px 60px rgba(0,0,0,0.16), 0 8px 24px rgba(0,0,0,0.08);
}

[data-theme="dark"] {
  --shadow-sm:    0 1px 2px rgba(0,0,0,0.20);
  --shadow-md:    0 4px 8px rgba(0,0,0,0.30);
  --shadow-lg:    0 8px 24px rgba(0,0,0,0.40);
  --shadow-modal: 0 20px 60px rgba(0,0,0,0.50);
}

/* ── Animaciones y transiciones ─────────────────────────────────────────── */
:root {
  --duration-fast:   100ms;
  --duration-base:   200ms;
  --duration-slow:   350ms;
  --ease-default:    cubic-bezier(0.4, 0, 0.2, 1);
  --ease-out:        cubic-bezier(0, 0, 0.2, 1);
  --ease-in:         cubic-bezier(0.4, 0, 1, 1);
  --ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1); /* rebote sutil */
}

/* Respetar prefers-reduced-motion — SIEMPRE incluir esto */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* ── Scrollbar custom ────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--color-scrollbar-track); }
::-webkit-scrollbar-thumb {
  background: var(--color-scrollbar-thumb);
  border-radius: 99px;
}

/* ── Keyframes ───────────────────────────────────────────────────────────── */

/* Shimmer para progress bar indeterminada */
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}

/* Entrada de ítems en lista */
@keyframes slideInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0);   }
}

/* Check de completado */
@keyframes checkDraw {
  from { stroke-dashoffset: 24; }
  to   { stroke-dashoffset: 0;  }
}

/* Fade in general */
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* Scale in para modales */
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.96); }
  to   { opacity: 1; transform: scale(1);    }
}

/* ── Clases de animación reutilizables ───────────────────────────────────── */
.animate-slide-in-up {
  animation: slideInUp var(--duration-base) var(--ease-out) forwards;
}

.animate-fade-in {
  animation: fadeIn var(--duration-base) var(--ease-out) forwards;
}

.animate-scale-in {
  animation: scaleIn var(--duration-base) var(--ease-spring) forwards;
}

/* Shimmer progress bar — aplicar a la barra cuando status === 'processing' */
.progress-shimmer {
  background: linear-gradient(
    90deg,
    var(--color-accent) 0%,
    var(--color-accent-hover) 50%,
    var(--color-accent) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
```

---

## 3. Tailwind Config (`tailwind.config.ts`)

```typescript
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
```

---

## 4. Utilidad `cn` (`src/lib/cn.ts`)

```typescript
// Helper estándar para combinar clases Tailwind de forma segura.
// Siempre usar cn() en componentes — nunca concatenar strings de clases.
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

---

## 5. Aplicación del tema en el DOM (`src/hooks/useSystemTheme.ts`)

```typescript
// Este hook gestiona la aplicación del tema en el elemento <html>.
// Debe montarse en App.tsx como efecto de arranque.
//
// Reglas:
// 1. Al iniciar, leer preferencia guardada (useAppStore → theme).
// 2. Si theme === 'system', escuchar window.matchMedia('(prefers-color-scheme: dark)').
// 3. Si theme === 'light' | 'dark', aplicar directamente.
// 4. Aplicar: document.documentElement.setAttribute('data-theme', resolvedTheme)
// 5. Actualizar resolvedTheme en el store.
// 6. Limpiar el listener al desmontar.
//
// NUNCA agregar clases 'dark' al <html> — usar SOLO data-theme.
```

---

## 6. Paleta de colores de iconos de archivo

> Estos colores son clases Tailwind que deben coincidir con las del mapa
> `FILE_ICON_MAP` definido en `src/types/index.ts`.

| Tipo | Clase Tailwind | Hex referencial |
|------|---------------|----------------|
| PDF | `text-red-500` | #EF4444 |
| Word | `text-blue-500` | #3B82F6 |
| Excel | `text-green-500` | #22C55E |
| PowerPoint | `text-orange-500` | #F97316 |
| HTML / CSV | `text-gray-400` | #9CA3AF |
| Audio | `text-purple-500` | #A855F7 |
| Video | `text-indigo-500` | #6366F1 |

> Usar `text-opacity-90` en dark mode para suavizar levemente los colores.

---

## 7. Especificación de botones

Existen 3 variantes de botón. No crear más variantes sin justificación.

### Primary (acción principal)
```
background:   var(--color-accent)
color:        var(--color-text-on-accent)
hover bg:     var(--color-accent-hover)
active bg:    var(--color-accent-active)
border:       none
border-radius: var(--radius-md)
height:       44px
padding:      0 20px
font-weight:  var(--font-semibold)
font-size:    var(--text-base)
transition:   background var(--duration-fast) var(--ease-default)
```

### Secondary (acción secundaria)
```
background:   var(--color-surface)
color:        var(--color-text-primary)
hover bg:     var(--color-surface-secondary)
border:       1px solid var(--color-border-strong)
border-radius: var(--radius-md)
height:       44px
padding:      0 20px
font-weight:  var(--font-medium)
```

### Ghost (acción terciaria / links)
```
background:   transparent
color:        var(--color-accent)
hover bg:     var(--color-accent-subtle)
border:       none
border-radius: var(--radius-md)
height:       36px
padding:      0 12px
font-weight:  var(--font-medium)
font-size:    var(--text-sm)
```

### Destructive (cancelar / eliminar)
```
Igual que Secondary pero:
color:        var(--color-error)
hover bg:     var(--color-error-subtle)
border-color: var(--color-error)
```

### Estado disabled (todos los botones)
```
opacity:      0.4
cursor:       not-allowed
pointer-events: none
```

---

## 8. Especificación de badges de estado

Usados en FileItem y ProcessingFileItem.

| Estado | Fondo | Texto | Ícono Lucide |
|--------|-------|-------|-------------|
| `pending` | `var(--color-surface-secondary)` | `var(--color-text-tertiary)` | `Clock` (16px) |
| `processing` | `var(--color-accent-subtle)` | `var(--color-accent)` | spinner (16px) |
| `completed` | `var(--color-success-subtle)` | `var(--color-success)` | `CheckCircle` (16px) |
| `error` | `var(--color-error-subtle)` | `var(--color-error)` | `XCircle` (16px) |

Tamaño del badge: `height: 24px`, `padding: 0 8px`, `border-radius: var(--radius-sm)`, `font-size: var(--text-xs)`, `font-weight: var(--font-medium)`.

---

## 9. Especificación de progress bar

```
container:
  height:         4px
  border-radius:  var(--radius-sm)
  background:     var(--color-border)
  overflow:       hidden

fill (status === 'processing', progress indeterminado):
  height:         100%
  width:          100%
  class:          progress-shimmer  ← keyframe definido en index.css

fill (status === 'processing', con progress real):
  height:         100%
  width:          {progress}%
  background:     var(--color-accent)
  transition:     width 300ms var(--ease-out)

fill (status === 'completed'):
  width:          100%
  background:     var(--color-success)
  transition:     background var(--duration-fast)

fill (status === 'error'):
  width:          100%
  background:     var(--color-error)
```

---

## 10. Tipografía del preview de markdown

El panel de preview renderiza markdown con `react-markdown`. Aplicar estos estilos al contenedor:

```css
.markdown-preview {
  font-family: var(--font-family);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-text-primary);
}

.markdown-preview h1 { font-size: var(--text-2xl); font-weight: var(--font-bold);     margin: 0 0 16px; }
.markdown-preview h2 { font-size: var(--text-xl);  font-weight: var(--font-semibold); margin: 24px 0 12px; }
.markdown-preview h3 { font-size: var(--text-lg);  font-weight: var(--font-semibold); margin: 20px 0 8px; }
.markdown-preview p  { margin: 0 0 12px; }
.markdown-preview ul, .markdown-preview ol { padding-left: 24px; margin: 0 0 12px; }
.markdown-preview li { margin-bottom: 4px; }
.markdown-preview code {
  font-family: var(--font-family-mono);
  font-size: var(--text-sm);
  background: var(--color-surface-secondary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}
.markdown-preview pre {
  background: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  overflow-x: auto;
}
.markdown-preview pre code {
  background: none;
  padding: 0;
}
.markdown-preview table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 16px;
  font-size: var(--text-sm);
}
.markdown-preview th {
  background: var(--color-surface-secondary);
  padding: 8px 12px;
  text-align: left;
  font-weight: var(--font-semibold);
  border-bottom: 1px solid var(--color-border-strong);
}
.markdown-preview td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border);
}
.markdown-preview blockquote {
  border-left: 3px solid var(--color-accent);
  padding-left: 16px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}
.markdown-preview hr {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 24px 0;
}
.markdown-preview a {
  color: var(--color-accent);
  text-decoration: none;
}
.markdown-preview a:hover {
  text-decoration: underline;
}
```

---

## 11. shadcn/ui — Configuración (`components.json`)

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/cn",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

Componentes de shadcn/ui a instalar:
```bash
npx shadcn@latest add button progress badge dialog scroll-area tooltip
```

> **Nota:** Los componentes de shadcn/ui usarán las CSS custom properties del design system automáticamente si se configura el mapeo en `tailwind.config.ts`. Verificar que los tokens de shadcn (`--primary`, `--background`, etc.) estén mapeados a las variables de Markify en `index.css`.

---

## 12. Mapeo de variables shadcn → Markify

Añadir al `:root` de `index.css` para que shadcn funcione con el design system:

```css
:root {
  /* shadcn/ui requiere estas variables — mapear a los tokens de Markify */
  --background: 0 0% 100%;            /* blanco — sobreescrito por data-theme */
  --foreground: 0 0% 0%;
  --primary: 211 100% 50%;            /* #007AFF */
  --primary-foreground: 0 0% 100%;
  --secondary: 240 5% 96%;
  --secondary-foreground: 0 0% 0%;
  --muted: 240 5% 96%;
  --muted-foreground: 240 4% 46%;
  --border: 240 6% 10% / 12%;
  --ring: 211 100% 50%;
  --radius: 0.625rem;                 /* 10px = var(--radius-md) */
  --destructive: 4 90% 58%;          /* #FF3B30 */
}

[data-theme="dark"] {
  --background: 0 0% 11%;
  --foreground: 0 0% 100%;
  --primary: 211 100% 53%;           /* #0A84FF */
  --secondary: 0 0% 17%;
  --muted: 0 0% 17%;
  --muted-foreground: 240 5% 65%;
  --border: 0 0% 100% / 10%;
}
```
