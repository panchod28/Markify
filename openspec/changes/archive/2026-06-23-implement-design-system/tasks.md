## 1. CSS Design Tokens

- [x] 1.1 Replace `src/index.css` with base reset, Tailwind directives, and `:root` light mode color tokens (accent, semantic, surfaces, text, borders, drop zone, overlay, scrollbar)
- [x] 1.2 Add `[data-theme="dark"]` overrides for all color tokens
- [x] 1.3 Add typography tokens: system font stacks, Apple HIG font sizes (xs–3xl), weights, line heights
- [x] 1.4 Add 8px grid spacing tokens (`--space-1` through `--space-16`)
- [x] 1.5 Add border radius tokens (`--radius-sm` through `--radius-xl`)
- [x] 1.6 Add shadow tokens with dark mode overrides
- [x] 1.7 Add animation duration/easing tokens and `prefers-reduced-motion` media query
- [x] 1.8 Add custom scrollbar styles (Webkit)
- [x] 1.9 Add keyframes (shimmer, slideInUp, checkDraw, fadeIn, scaleIn) and reusable animation classes
- [x] 1.10 Add `.markdown-preview` styles for rendered markdown (headings, code, tables, blockquotes, links, etc.)

## 2. shadcn/ui CSS Variable Mapping

- [x] 2.1 Add shadcn-compatible CSS variables to `:root` in `index.css` (--background, --foreground, --primary, --secondary, --muted, --border, --ring, --radius, --destructive)
- [x] 2.2 Add `[data-theme="dark"]` overrides for shadcn variables

## 3. Tailwind Configuration

- [x] 3.1 Create `tailwind.config.ts` with `darkMode: ['attribute', '[data-theme="dark"]']`, content paths, and color mappings to CSS variables
- [x] 3.2 Map font families (`font-sans`, `font-mono`), font sizes (xs–3xl with line heights), border radii, box shadows, transition durations, and easing to CSS variables

## 4. Classname Utility

- [x] 4.1 Create `src/lib/cn.ts` with the `cn()` helper using `clsx` + `tailwind-merge`
- [x] 4.2 Remove `cn()` from `src/lib/utils.ts` (or remove the file if empty)

## 5. Theme Hook

- [x] 5.1 Create `src/hooks/useSystemTheme.ts` that reads `theme` from store, resolves `system` to `prefers-color-scheme`, and applies `data-theme` attribute to `<html>`
- [x] 5.2 Implement `matchMedia` listener for system theme changes when `theme === 'system'`
- [x] 5.3 Return cleanup function to remove listener on unmount

## 6. shadcn/ui Setup

- [x] 6.1 Create `components.json` at project root with TypeScript, CSS variables, neutral base, and correct path aliases
- [x] 6.2 Install shadcn/ui components: `button`, `progress`, `badge`, `dialog`, `scroll-area`, `tooltip`
