// ─── Categoría de archivo ─────────────────────────────────────────────────
// Determina qué herramienta usa el sidecar: markitdown o Whisper.
export type FileCategory = 'document' | 'audio';

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

// ─── Entidad principal: ConversionFile ────────────────────────────────────
export interface ConversionFile {
  id: string;
  originalName: string;
  sanitizedName: string;
  path: string;
  sizeBytes: number;
  formattedSize: string;
  category: FileCategory;
  extension: string;
  status: FileStatus;
  progress: number;
  errorMessage?: string;
  markdownContent?: string;
}

// ─── Eventos Tauri → Frontend ─────────────────────────────────────────────
export interface ConversionProgressEvent {
  fileId: string;
  status: FileStatus;
  progress: number;
  errorMessage?: string;
  markdownContent?: string;
}

export interface ModelDownloadProgressEvent {
  percent: number;
  downloadedMB: number;
  totalMB: number;
}

// ─── Resumen de conversión (computed) ─────────────────────────────────────
export interface ConversionSummary {
  total: number;
  completed: number;
  failed: number;
  pending: number;
}

// ─── Props de comandos Tauri ──────────────────────────────────────────────
export interface StartConversionPayload {
  files: Array<{
    id: string;
    path: string;
    category: FileCategory;
  }>;
  lang: ResolvedLanguage;
}

export interface SaveZipPayload {
  files: Array<{
    name: string;
    content: string;
  }>;
  suggestedName: string;
}

// ─── Constantes de extensiones soportadas ─────────────────────────────────
export const DOCUMENT_EXTENSIONS = [
  'pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'docx', 'doc', 'html', 'csv'
] as const;

export type DocumentExtension = typeof DOCUMENT_EXTENSIONS[number];

export const AUDIO_EXTENSIONS = [
  'mp3', 'mp4', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'aac'
] as const;

export type AudioExtension = typeof AUDIO_EXTENSIONS[number];

export const SUPPORTED_EXTENSIONS = [
  ...DOCUMENT_EXTENSIONS,
  ...AUDIO_EXTENSIONS,
] as const;

export type SupportedExtension = typeof SUPPORTED_EXTENSIONS[number];

// ─── Constantes de límites y configuración ────────────────────────────────
export const MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024;
export const MAX_TOTAL_BATCH_SIZE_BYTES = 2 * 1024 * 1024 * 1024;
export const MAX_FILES_PER_BATCH = 50;

export const WHISPER_MODEL_NAME = 'base';
export const WHISPER_MODEL_SIZE_MB = 145;

export const WINDOW_DEFAULT_WIDTH = 960;
export const WINDOW_DEFAULT_HEIGHT = 680;
export const WINDOW_MIN_WIDTH = 800;
export const WINDOW_MIN_HEIGHT = 600;

// ─── Mapa de iconos por extensión ─────────────────────────────────────────
export const FILE_ICON_MAP: Record<SupportedExtension, {
  icon: string;
  colorClass: string;
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
};
