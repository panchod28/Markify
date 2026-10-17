# Spec 01 — TypeScript Types, Constants & Enums
> Markify — Fuente de verdad de todos los tipos compartidos del frontend.
> Archivo destino: `src/types/index.ts`
> Este archivo debe importarse en todo el proyecto. Nunca redefinir tipos localmente.

---

## 1. Enums y union types base

```typescript
// ─── Categoría de archivo ─────────────────────────────────────────────────
// Determina qué herramienta usa el sidecar: markitdown, Whisper u OCR (imágenes).
export type FileCategory = 'document' | 'audio' | 'image';

// ─── Estado de conversión de un archivo ──────────────────────────────────
export type FileStatus =
  | 'pending'      // En cola, sin procesar aún
  | 'processing'   // El sidecar lo está procesando ahora mismo
  | 'completed'    // Conversión exitosa — markdownContent disponible
  | 'error';       // Falló — errorMessage disponible

// ─── Estado global de la aplicación ──────────────────────────────────────
// Controla qué vista renderiza App.tsx
export type AppState =
  | 'empty'         // Sin archivos. Muestra DropZone grande.
  | 'files-ready'   // Archivos cargados. Muestra FileList + botón Convertir.
  | 'processing'    // Conversión en curso. Muestra ProcessingView.
  | 'results';      // Terminó (total o parcial). Muestra ResultsView.

// ─── Tema visual ─────────────────────────────────────────────────────────
export type Theme = 'light' | 'dark' | 'system';
// 'system' = leer prefers-color-scheme del OS
export type ResolvedTheme = 'light' | 'dark';
// ResolvedTheme nunca es 'system' — es el valor efectivo aplicado al DOM

// ─── Idioma de la interfaz ────────────────────────────────────────────────
export type Language = 'en' | 'es' | 'system';
// 'system' = leer navigator.language del OS
export type ResolvedLanguage = 'en' | 'es';

// ─── Modo de vista del preview ────────────────────────────────────────────
export type PreviewViewMode = 'rendered' | 'raw';
// 'rendered' = ReactMarkdown renderizado
// 'raw'      = <pre><code> con el markdown crudo
```

---

## 2. Entidad principal: ConversionFile

```typescript
// Representa un archivo en cualquier punto del ciclo de vida de la app.
// Se crea al añadir un archivo (addFiles) y se muta durante la conversión.
export interface ConversionFile {
  // ─── Identidad ───────────────────────────────────────────────────────────
  id: string;
  // UUID v4 generado en el cliente con crypto.randomUUID().
  // Nunca reutilizar IDs entre sesiones.

  // ─── Metadatos del archivo original ──────────────────────────────────────
  originalName: string;
  // Nombre completo con extensión tal como viene del OS.
  // Ejemplo: "Mi Presentación 2024.pptx"

  sanitizedName: string;
  // Nombre limpio que tendrá el .md de salida.
  // Calculado en el frontend con sanitizeFilename() al añadir el archivo.
  // Ejemplo: "mi_presentacion_2024.md"
  // Ver spec 09-pipeline.md § Sanitización para el algoritmo exacto.

  path: string;
  // Ruta absoluta al archivo en el disco del usuario.
  // En Tauri, obtenida del objeto File mediante window.__TAURI__.path o
  // pasada directamente desde el file picker nativo.

  sizeBytes: number;
  // Tamaño en bytes. Usado para validaciones de límite.

  formattedSize: string;
  // Calculado UNA VEZ al añadir, nunca recalcular.
  // Formato: "1.2 KB", "3.4 MB", "1.2 GB"
  // Usar la función formatFileSize() de src/lib/formatters.ts

  category: FileCategory;
  // 'document' para extensiones de markitdown
  // 'audio'    para extensiones de Whisper
  // Calculado con getFileCategory(extension) de src/lib/fileUtils.ts

  extension: string;
  // Extensión en minúsculas SIN el punto.
  // Ejemplo: "pdf", "mp3", "xlsx"

  // ─── Estado de la conversión ──────────────────────────────────────────────
  status: FileStatus;
  // Valor inicial siempre: 'pending'

  progress: number;
  // Rango: 0 a 100. Valor inicial: 0.
  // Para documentos: salta de 0 a 100 al completarse (no hay progreso parcial real).
  // Para audio: Whisper emite progreso parcial — actualizar en tiempo real.

  // ─── Resultados (presentes solo cuando aplica) ────────────────────────────
  errorMessage?: string;
  // Solo presente cuando status === 'error'.
  // Texto ya traducido al idioma activo (el sidecar recibe el lang y devuelve el mensaje correcto).
  // Nunca mostrar errores técnicos/stack traces al usuario.

  markdownContent?: string;
  // Solo presente cuando status === 'completed'.
  // Contenido markdown completo listo para mostrar y guardar.
  // Puede ser una cadena muy larga (documentos grandes).
}
```

---

## 3. Eventos Tauri → Frontend

```typescript
// Payload del evento 'conversion:file-update'
// Emitido por Rust cada vez que el sidecar reporta cambio en un archivo.
export interface ConversionProgressEvent {
  fileId: string;           // Coincide con ConversionFile.id
  status: FileStatus;       // Nuevo status
  progress: number;         // Nuevo progress (0-100)
  errorMessage?: string;    // Solo si status === 'error'
  markdownContent?: string; // Solo si status === 'completed'
  warnings?: ConversionWarning[]; // Solo en el file_result de un archivo completado con avisos
}

// Aviso no fatal de una conversión (OCR). El texto ya llega localizado desde el sidecar (según `lang`).
// `page` es null en avisos de todo el archivo (p. ej. líneas descartadas por baja confianza).
export interface ConversionWarning {
  page: number | null;
  stage: string;   // open | decode | classify | render | ocr | layout | assemble
  code: string;    // page_failed | low_confidence_dropped | frames_skipped
  message: string;
}

// Payload del evento 'model:download-progress'
// Emitido durante la descarga del modelo Whisper.
export interface ModelDownloadProgressEvent {
  percent: number;          // 0-100
  downloadedMB: number;     // Bytes descargados convertidos a MB (1 decimal)
  totalMB: number;          // Tamaño total en MB (1 decimal)
}
```

---

## 4. Resumen de conversión (computed)

```typescript
// Calculado desde los archivos del store, nunca almacenado.
// Usar como selector en componentes que lo necesiten.
export interface ConversionSummary {
  total: number;      // files.length
  completed: number;  // files.filter(f => f.status === 'completed').length
  failed: number;     // files.filter(f => f.status === 'error').length
  pending: number;    // files.filter(f => f.status === 'pending').length
}
```

---

## 5. Props de comandos Tauri

```typescript
// Argumento para el comando 'start_conversion'
export interface StartConversionPayload {
  files: Array<{
    id: string;
    path: string;
    category: FileCategory;
  }>;
  lang: ResolvedLanguage; // Para que el sidecar devuelva errores en el idioma correcto
}

// Argumento para el comando 'save_zip'
export interface SaveZipPayload {
  files: Array<{
    name: string;    // sanitizedName del ConversionFile (ya incluye .md)
    content: string; // markdownContent
  }>;
  suggestedName: string; // "conversion_2026-06-22_14-30.zip"
}
```

---

## 6. Constantes de extensiones soportadas

```typescript
// ─── Extensiones de documentos (procesados por markitdown) ───────────────
export const DOCUMENT_EXTENSIONS = [
  'pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'docx', 'doc', 'html', 'csv'
] as const;

export type DocumentExtension = typeof DOCUMENT_EXTENSIONS[number];

// ─── Extensiones de audio/video (procesados por Whisper) ─────────────────
export const AUDIO_EXTENSIONS = [
  'mp3', 'mp4', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'aac'
] as const;

export type AudioExtension = typeof AUDIO_EXTENSIONS[number];

// ─── Extensiones de imagen (OCR local) ─────────────────────────────────────
export const IMAGE_EXTENSIONS = [
  'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tif', 'tiff'
] as const;

export type ImageExtension = typeof IMAGE_EXTENSIONS[number];

// ─── Unión de todas las extensiones soportadas ────────────────────────────
export const SUPPORTED_EXTENSIONS = [
  ...DOCUMENT_EXTENSIONS,
  ...AUDIO_EXTENSIONS,
  ...IMAGE_EXTENSIONS,
] as const;

export type SupportedExtension = typeof SUPPORTED_EXTENSIONS[number];
```

---

## 7. Constantes de límites y configuración

```typescript
// ─── Límites de validación (aplicados en el frontend al añadir archivos) ──
export const MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024;        // 500 MB por archivo
export const MAX_TOTAL_BATCH_SIZE_BYTES = 2 * 1024 * 1024 * 1024; // 2 GB total del batch
export const MAX_FILES_PER_BATCH = 50;                        // máximo 50 archivos

// ─── Modelo de Whisper ────────────────────────────────────────────────────
export const WHISPER_MODEL_NAME = 'base';    // No cambiar en v1
export const WHISPER_MODEL_SIZE_MB = 145;    // Para mostrar en el modal de descarga

// ─── Dimensiones de ventana ───────────────────────────────────────────────
export const WINDOW_DEFAULT_WIDTH = 960;
export const WINDOW_DEFAULT_HEIGHT = 680;
export const WINDOW_MIN_WIDTH = 800;
export const WINDOW_MIN_HEIGHT = 600;
```

---

## 8. Mapa de iconos por extensión

```typescript
// Usado en FileItem, ProcessingFileItem y ResultFileItem
// Importar los iconos de lucide-react según esta tabla.
export const FILE_ICON_MAP: Record<SupportedExtension, {
  icon: string;        // nombre exacto del ícono en lucide-react
  colorClass: string;  // clase Tailwind de color
}> = {
  // Documentos
  pdf:  { icon: 'FileText',     colorClass: 'text-red-500'    },
  docx: { icon: 'FileText',     colorClass: 'text-blue-500'   },
  doc:  { icon: 'FileText',     colorClass: 'text-blue-500'   },
  xlsx: { icon: 'Sheet',        colorClass: 'text-green-500'  },
  xls:  { icon: 'Sheet',        colorClass: 'text-green-500'  },
  pptx: { icon: 'Presentation', colorClass: 'text-orange-500' },
  ppt:  { icon: 'Presentation', colorClass: 'text-orange-500' },
  html: { icon: 'FileCode',     colorClass: 'text-gray-500'   },
  csv:  { icon: 'FileCode',     colorClass: 'text-gray-500'   },
  // Audio
  mp3:  { icon: 'Music',        colorClass: 'text-purple-500' },
  wav:  { icon: 'Music',        colorClass: 'text-purple-500' },
  m4a:  { icon: 'Music',        colorClass: 'text-purple-500' },
  flac: { icon: 'Music',        colorClass: 'text-purple-500' },
  aac:  { icon: 'Music',        colorClass: 'text-purple-500' },
  ogg:  { icon: 'Music',        colorClass: 'text-purple-500' },
  // Video
  mp4:  { icon: 'Video',        colorClass: 'text-indigo-500' },
  webm: { icon: 'Video',        colorClass: 'text-indigo-500' },
  // Imágenes (icono `Image` de lucide-react, importado como ImageIcon; mismo color que el resto)
  // png, jpg, jpeg, webp, bmp, tif, tiff → { icon: 'Image' }
};
```

---

## 9. Funciones utilitarias de tipos (src/lib/fileUtils.ts)

```typescript
// Extrae la extensión de un nombre de archivo en minúsculas sin punto.
// "Mi Archivo.PDF" → "pdf"
// "audio.MP3"      → "mp3"
export function getExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() ?? '';
}

// Determina si una extensión está soportada.
export function isSupportedExtension(ext: string): ext is SupportedExtension {
  return (SUPPORTED_EXTENSIONS as readonly string[]).includes(ext);
}

// Determina la categoría de un archivo por su extensión.
// Retorna null si la extensión no está soportada.
export function getFileCategory(ext: string): FileCategory | null {
  if ((DOCUMENT_EXTENSIONS as readonly string[]).includes(ext)) return 'document';
  if ((AUDIO_EXTENSIONS as readonly string[]).includes(ext)) return 'audio';
  if ((IMAGE_EXTENSIONS as readonly string[]).includes(ext)) return 'image';
  return null;
}
```

---

## 10. Función de formateo de tamaño (src/lib/formatters.ts)

```typescript
// Convierte bytes a string legible con 1 decimal.
// 0           → "0 B"
// 1023        → "1023 B"
// 1024        → "1.0 KB"
// 1536        → "1.5 KB"
// 1048576     → "1.0 MB"
// 1073741824  → "1.0 GB"
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const value = bytes / Math.pow(1024, i);
  return i === 0
    ? `${value} B`
    : `${value.toFixed(1)} ${units[i]}`;
}

// Genera el nombre sugerido para el ZIP de salida.
// Ejemplo: "conversion_2026-06-22_14-30.zip"
export function generateZipName(): string {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);        // "2026-06-22"
  const time = now.toTimeString().slice(0, 5).replace(':', '-'); // "14-30"
  return `conversion_${date}_${time}.zip`;
}
```

---

## 11. Wrapper tipado de Tauri (src/lib/tauri.ts)

```typescript
import { invoke } from '@tauri-apps/api/core';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import type {
  StartConversionPayload,
  SaveZipPayload,
  ConversionProgressEvent,
  ModelDownloadProgressEvent,
  FileCategory,
  ResolvedLanguage,
} from '@/types';

// ─── Comandos ─────────────────────────────────────────────────────────────

export const tauriCommands = {
  startConversion: (payload: StartConversionPayload): Promise<void> =>
    invoke('start_conversion', payload),

  cancelConversion: (): Promise<void> =>
    invoke('cancel_conversion'),

  saveMarkdown: (content: string, suggestedName: string): Promise<string | null> =>
    invoke('save_markdown', { content, suggestedName }),

  saveZip: (payload: SaveZipPayload): Promise<string | null> =>
    invoke('save_zip', payload),

  openInFolder: (filePath: string): Promise<void> =>
    invoke('open_in_folder', { filePath }),

  checkWhisperModel: (): Promise<boolean> =>
    invoke('check_whisper_model'),

  downloadWhisperModel: (): Promise<void> =>
    invoke('download_whisper_model'),

  getAppVersion: (): Promise<string> =>
    invoke('get_app_version'),
};

// ─── Eventos ──────────────────────────────────────────────────────────────

export const tauriEvents = {
  onFileUpdate: (handler: (event: ConversionProgressEvent) => void): Promise<UnlistenFn> =>
    listen<ConversionProgressEvent>('conversion:file-update', e => handler(e.payload)),

  onModelDownloadProgress: (handler: (event: ModelDownloadProgressEvent) => void): Promise<UnlistenFn> =>
    listen<ModelDownloadProgressEvent>('model:download-progress', e => handler(e.payload)),

  onModelDownloadComplete: (handler: () => void): Promise<UnlistenFn> =>
    listen('model:download-complete', handler),

  onModelDownloadError: (handler: (msg: string) => void): Promise<UnlistenFn> =>
    listen<{ message: string }>('model:download-error', e => handler(e.payload.message)),

  onConversionComplete: (handler: () => void): Promise<UnlistenFn> =>
    listen('conversion:complete', handler),

  onConversionCancelled: (handler: () => void): Promise<UnlistenFn> =>
    listen('conversion:cancelled', handler),
};
```
