## Context

Markify tiene types (spec 01) y design system (spec 02). Los stores son el paso 3 del orden de implementación. La spec `03-stores.md` define 3 stores Zustand + 1 hook de eventos + 1 función utilitaria. Zustand fue elegido por encima de Redux/Context por su API mínima, ausencia de boilerplate y soporte nativo para selectors con `shallow` equality.

Dependencias ya existentes: `zustand` (instalado), `src/types/index.ts`, `src/lib/fileUtils.ts`, `src/lib/formatters.ts`, `src/lib/tauri.ts`.

Dependencias nuevas: `@tauri-apps/plugin-store` para persistencia cross-platform, `src/lib/sanitizer.ts` para sanitización de nombres de archivo.

## Goals / Non-Goals

**Goals:**
- Implementar `useAppStore` con persistencia vía tauri-plugin-store (theme, language)
- Implementar `useConversionStore` con máquina de estados `appState`, validación de archivos, y orquestación de conversión
- Implementar `usePreviewStore` con selección de archivo y toggle de modo
- Implementar `useTauriEvents` hook para conectar eventos backend → acciones del store
- Implementar `sanitizeFilename()` requerida por el conversion store
- Actualizar `useSystemTheme` para importar correctamente de `useAppStore`

**Non-Goals:**
- Implementar componentes visuales (spec 06)
- Implementar pantallas de la app (spec 07)
- Implementar comandos Rust (spec 04)
- Crear el componente LanguageToggle que usa `setLanguage`

## Decisions

1. **Tres stores separados en lugar de uno monolítico**: `useAppStore` (preferencias), `useConversionStore` (conversión), `usePreviewStore` (preview). Cada store tiene una responsabilidad clara. Alternativa: un store único con slices (más complejo de mantener, Zustand recomienda stores separados).

2. **`tauri-plugin-store` en lugar de localStorage**: localStorage no es confiable en Tauri (WebView puede limpiarlo). `tauri-plugin-store` persiste en disco del sistema de archivos nativo. Solo `useAppStore` persiste (theme, language); los otros son efímeros.

3. **Getters computados dentro del store**: `summary`, `completedFiles`, `totalBatchSizeBytes`, etc. se calculan como getters de clase en lugar de estado derivado. Esto evita desincronización. Alternativa: selectors externos (más boilerplate, mismo resultado).

4. **Acciones internas prefijadas con `_`**: `_handleFileUpdate`, `_initialize`, etc. son llamadas solo desde hooks (`useTauriEvents`, `useSystemTheme`). Convención clara: componentes nunca llaman acciones `_`.

5. **`sanitizeFilename()` separada en `src/lib/sanitizer.ts`**: Aunque la spec 09-pipeline.md define la sanitización completa, el conversion store la necesita ahora. Se implementa la función básica de spec 09 § Sanitización. El algoritmo completo puede refinarse al implementar spec 09.

6. **`useTauriEvents` como hook de montaje único en App.tsx**: Todos los listeners se registran al montar y se limpian al desmontar. Usa `useConversionStore.getState()` para acceder al store sin crear suscripciones React (importante: no queremos re-renders por eventos).

7. **Validación no lanza excepciones**: `addFiles()` acumula errores en `validationErrors[]`. Los componentes los muestran como toast. Esto permite feedback completo (ej: "3 archivos no soportados, 1 demasiado grande").

## Risks / Trade-offs

- **[Bajo] `sanitizeFilename()` puede divergir de spec 09**: La implementación actual es la básica de spec 09. Mitigación: al implementar spec 09, actualizar `sanitizer.ts` con el algoritmo completo.
- **[Bajo] `useTauriEvents` usa `getState()`**: Esto evita re-renders pero significa que el hook no puede reaccionar a cambios de estado. Es intencional — los listeners solo despachan acciones.
- **[Medio] `@tauri-apps/plugin-store` requiere configuración Rust**: El plugin debe registrarse en `src-tauri/Cargo.toml` y `src-tauri/src/lib.rs`. Esto está fuera del scope de este cambio (spec 03) pero es necesario para que la persistencia funcione. Se documentará en las tareas.
