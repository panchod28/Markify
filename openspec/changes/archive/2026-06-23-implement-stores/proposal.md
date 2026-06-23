## Why

Markify necesita estado global para gestionar preferencias de usuario, archivos en conversión y selección de preview. Los tipos ya existen (spec 01), el design system está definido (spec 02). Ahora los stores de Zustand son el paso 3 del orden de implementación y son prerequisito para componentes (spec 06) y pantallas (spec 07). Sin stores, ninguna interacción de usuario funciona.

## What Changes

- Crear `src/stores/useAppStore.ts` — store persistido con `tauri-plugin-store` para `theme` y `language`
- Crear `src/stores/useConversionStore.ts` — store efímero con máquina de estados `appState`, gestión de archivos, validación, conversión y modelo Whisper
- Crear `src/stores/usePreviewStore.ts` — store efímero para selección de archivo en preview y modo de vista
- Crear `src/lib/sanitizer.ts` — función `sanitizeFilename()` referenciada por `useConversionStore`
- Crear `src/hooks/useTauriEvents.ts` — hook que conecta eventos Tauri con acciones internas del store
- Añadir dependencia `@tauri-apps/plugin-store` para persistencia cross-platform

## Capabilities

### New Capabilities

- `app-store`: Store de preferencias globales persistido (theme, language) con inicialización desde disco
- `conversion-store`: Store de ciclo de conversión con máquina de estados, validación de archivos, getters computados y acciones del modelo Whisper
- `preview-store`: Store de selección de archivo para preview con toggle de modo rendered/raw
- `sanitizer`: Función `sanitizeFilename()` requerida por el conversion store para limpiar nombres de archivo
- `tauri-events-hook`: Hook `useTauriEvents()` que conecta eventos Tauri → acciones internas del store

### Modified Capabilities

- `theme-hook`: `useSystemTheme` ahora puede importar correctamente de `useAppStore` (antes fallaba porque el store no existía)

## Impact

- **Crea**: `src/stores/useAppStore.ts`, `src/stores/useConversionStore.ts`, `src/stores/usePreviewStore.ts`, `src/lib/sanitizer.ts`, `src/hooks/useTauriEvents.ts`
- **Modifica**: `src/hooks/useSystemTheme.ts` — ahora resuelve la importación de `useAppStore`
- **Dependencias nuevas**: `@tauri-apps/plugin-store` (npm)
- **Dependencias existentes usadas**: `zustand`, `@/types`, `@/lib/fileUtils`, `@/lib/formatters`, `@/lib/tauri`
