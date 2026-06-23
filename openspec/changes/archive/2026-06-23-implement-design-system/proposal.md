## Why

Markify necesita un design system coherente antes de implementar componentes visuales. La spec `02-design-system.md` define todos los tokens CSS, la configuración de Tailwind, el hook de tema y la integración con shadcn/ui. Sin estas bases, cada componente tendría estilos hardcodeados, el dark mode sería inconsistente y shadcn/ui no funcionaría correctamente con los tokens del proyecto.

## What Changes

- Reemplazar `src/index.css` actual con CSS custom properties completas: colores light/dark, tipografía (escala Apple HIG), espaciado (grilla de 8px), border-radius, sombras, animaciones, keyframes, scrollbar custom y reset base
- Crear/actualizar `tailwind.config.ts` con mapeo de CSS variables a clases Tailwind y configuración `darkMode: ['attribute', '[data-theme="dark"]']`
- Mover la función `cn()` de `src/lib/utils.ts` a `src/lib/cn.ts` para alinear con la spec y shadcn/ui
- Crear `src/hooks/useSystemTheme.ts` — hook que aplica `data-theme` al `<html>` y reacciona a cambios de sistema
- Crear `components.json` para shadcn/ui con paths correctos
- Añadir mapeo de variables shadcn (`--background`, `--primary`, etc.) a tokens Markify en `index.css`
- Instalar componentes shadcn/ui: `button`, `progress`, `badge`, `dialog`, `scroll-area`, `tooltip`

## Capabilities

### New Capabilities

- `css-tokens`: CSS custom properties con light/dark mode para colores, tipografía, espaciado, sombras, animaciones, scrollbar y keyframes
- `tailwind-config`: Configuración de Tailwind CSS que mapea tokens CSS a clases utilitarias
- `theme-hook`: Hook `useSystemTheme` que gestiona el atributo `data-theme` en el DOM y reacciona a `prefers-color-scheme`
- `shadcn-setup`: Configuración de shadcn/ui (`components.json`), mapeo de variables CSS y componentes base

### Modified Capabilities

N/A — proyecto greenfield, sin capacidades existentes que modificar.

## Impact

- **Modifica**: `src/index.css` (reemplazo completo), `tailwind.config.ts` (creación o reemplazo)
- **Crea**: `src/lib/cn.ts`, `src/hooks/useSystemTheme.ts`, `components.json`
- **Obsoleta**: `src/lib/utils.ts` — la función `cn()` se mueve a `src/lib/cn.ts`
- **Dependencias npm**: `tailwind-merge`, `clsx` (ya instalados), `class-variance-authority` (requerido por shadcn/ui)
- **Dependencias shadcn/ui**: `button`, `progress`, `badge`, `dialog`, `scroll-area`, `tooltip`
