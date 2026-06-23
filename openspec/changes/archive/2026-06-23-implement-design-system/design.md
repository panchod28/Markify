## Context

Markify es una app desktop con Tauri v2 + React 18. Opera sobre macOS, Windows y Linux. Cada SO tiene su propio conjunto de fuentes nativas. El spec `02-design-system.md` define un design system Apple-quality que debe sentirse nativo en cada plataforma usando CSS custom properties que se adaptan a light/dark mode.

Estado actual: `src/index.css` tiene Tailwind directives base pero sin tokens. `src/lib/utils.ts` tiene `cn()`. No existe `tailwind.config.ts` ni `components.json`. La app aún no tiene sistema de temas.

## Goals / Non-Goals

**Goals:**
- Definir todos los tokens visuales como CSS custom properties en `:root` y `[data-theme="dark"]`
- Configurar Tailwind para mapear CSS variables a clases utilitarias
- Aplicar dark mode vía atributo `data-theme` en `<html>` (no clase `dark`)
- Proveer hook `useSystemTheme` que sincronice tema del store con el DOM
- Configurar shadcn/ui con los paths correctos y mapeo de variables
- Respetar `prefers-reduced-motion` deshabilitando todas las animaciones
- Mover `cn()` a `src/lib/cn.ts` para coincidir con el alias de shadcn/ui

**Non-Goals:**
- Implementar los componentes visuales concretos (FileItem, DropZone, etc.) — eso es spec 06
- Implementar stores (spec 03) — aunque useSystemTheme usará el store, este cambio solo crea el hook
- Crear botones o badges custom — se usarán los de shadcn/ui

## Decisions

1. **CSS custom properties como source of truth**: Todas las variables se definen en CSS y Tailwind las referencia con `var()`. Los componentes nunca hardcodean colores. Alternativa: definir colores directamente en Tailwind config (más rígido, no permite cambiar en runtime).

2. **`data-theme` en lugar de clase `dark`**: Tauri no tiene acceso al DOM de Tailwind para toggle de clases. Usar un atributo `data-theme` en `<html>` permite que el sidecar o el frontend cambien el tema sin manipular clases de Tailwind. Además, `[data-theme="dark"]` es explícito y no colisiona con otras herramientas.

3. **Fuentes del sistema sin Google Fonts**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Ubuntu'` cubre las 3 plataformas sin descargas adicionales. Esto reduce bundle size, elimina FOUT y se siente nativo.

4. **Grilla de 8px (`--space-*`)**: Cada valor es múltiplo de 4px (8px preferido). Consistente con Apple HIG y fácil de recordar. Los componentes usarán `var(--space-N)` para padding/margin/gap.

5. **`cn()` en `src/lib/cn.ts`**: shadcn/ui espera `utils` en `@/lib/cn`. Mantenerlo separado de `utils.ts` (que podría crecer con helpers no relacionados a Tailwind). La función `cn()` es idéntica a la actual, solo cambia de archivo.

6. **shadcn/ui se instala con sus propias CSS variables mapeadas a las de Markify**: En lugar de modificar componentes shadcn, mapeamos `--background`, `--primary`, etc. en `index.css`. Esto permite actualizar shadcn sin conflictos.

## Risks / Trade-offs

- **[Bajo] `src/lib/utils.ts` queda vacío tras mover `cn()`**: Se puede eliminar o mantener para futuros helpers. Se mantendrá con un comentario hasta que spec 03 u otras specs añadan utilidades.
- **[Bajo] shadcn/ui CSS variables deben mantenerse sincronizadas**: Si shadcn añade nuevas variables en futuras versiones, habrá que mapearlas. Mitigación: documentar en el archivo qué variables están mapeadas.
- **[Bajo] `prefers-reduced-motion` puede interferir con animaciones de Framer Motion**: Framer Motion respeta `prefers-reduced-motion` nativamente si se configura, pero el override CSS global podría causar conflicto. Mitigación: verificar compatibilidad al implementar componentes animados (spec 06).
- **[N/A] Sin migración**: Proyecto greenfield, no hay usuarios existentes.
