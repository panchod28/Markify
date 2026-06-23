## Why

Markify es un proyecto greenfield sin código fuente. La spec `01-types.md` define toda la tipificación compartida del frontend: enums, interfaces, constantes de configuración y utilidades. Estos tipos son la base sobre la que se construyen stores, componentes, pantallas y comandos Tauri. Implementarlos primero es requisito para que el resto del desarrollo compile y mantenga consistencia tipográfica.

## What Changes

- Crear `src/types/index.ts` con todos los type aliases e interfaces (`FileCategory`, `FileStatus`, `AppState`, `Theme`, `Language`, `ConversionFile`, eventos de progreso, payloads de comandos, `ConversionSummary`, `FILE_ICON_MAP`)
- Crear `src/types/index.ts` con las constantes de extensión (`DOCUMENT_EXTENSIONS`, `AUDIO_EXTENSIONS`, `SUPPORTED_EXTENSIONS`) y constantes de configuración (`MAX_FILE_SIZE_BYTES`, `WHISPER_MODEL_NAME`, dimensiones de ventana, etc.)
- Crear `src/lib/fileUtils.ts` con `getExtension()`, `isSupportedExtension()`, `getFileCategory()`
- Crear `src/lib/formatters.ts` con `formatFileSize()` y `generateZipName()`
- Crear `src/lib/tauri.ts` con wrappers tipados para todos los comandos Tauri y listeners de eventos

## Capabilities

### New Capabilities

- `types-core`: TypeScript types, enums, interfaces y constantes de configuración del frontend
- `file-utils`: Utilidades de detección de extensión y categorización de archivos
- `format-utils`: Funciones de formateo de tamaño de archivo y generación de nombres ZIP
- `tauri-typed-wrapper`: Wrappers tipados para invoke de comandos Tauri y listen de eventos

### Modified Capabilities

N/A — proyecto greenfield, sin capacidades existentes que modificar.

## Impact

- **Nuevos archivos**: `src/types/index.ts`, `src/lib/fileUtils.ts`, `src/lib/formatters.ts`, `src/lib/tauri.ts`
- **Dependencias**: `@tauri-apps/api/core` (invoke), `@tauri-apps/api/event` (listen, UnlistenFn) — se asumen disponibles como dependencias del proyecto Tauri
- **Exportación central**: todos los tipos se reexportan desde `src/types/index.ts` para que el resto del proyecto los consuma con `import type { ... } from '@/types'`
