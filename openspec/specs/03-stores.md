# Spec 03 — Zustand Stores
> Markify — Estado global de la aplicación.
> Archivos destino: `src/stores/useAppStore.ts`, `src/stores/useConversionStore.ts`, `src/stores/usePreviewStore.ts`
> Dependencias de tipos: spec `01-types.md`

---

## Reglas generales

1. **Tres stores separados.** No mezclar responsabilidades.
2. **Zustand puro** — no usar Context ni Redux. Importar directamente con el hook.
3. **Persistencia** con `tauri-plugin-store` (no localStorage) para cross-platform reliability.
   - Solo `useAppStore` persiste: `theme` y `language`.
   - Los otros stores son efímeros (se reinician al cerrar la app).
4. **Acciones con nombre en imperativo** (`addFiles`, no `filesAdded`).
5. **Los selectors computed** (como `summary`) se calculan dentro del store como getters, no como estado derivado separado.
6. Las acciones prefijadas con `_` son **internas** — solo llamarlas desde hooks, nunca desde componentes directamente.

---

## 1. `useAppStore` — Preferencias globales

```typescript
// src/stores/useAppStore.ts
import { create } from 'zustand';
import { Store } from '@tauri-apps/plugin-store';
import type { Theme, ResolvedTheme, Language, ResolvedLanguage } from '@/types';

// ─── Interfaz pública ─────────────────────────────────────────────────────

interface AppStore {
  // Estado
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  language: Language;
  resolvedLanguage: ResolvedLanguage;

  // Acciones públicas
  setTheme: (theme: Theme) => Promise<void>;
  setLanguage: (lang: Language) => Promise<void>;

  // Acciones internas (llamar solo desde useSystemTheme y i18n/index.ts)
  _setResolvedTheme: (theme: ResolvedTheme) => void;
  _setResolvedLanguage: (lang: ResolvedLanguage) => void;

  // Inicialización — llamar UNA VEZ en App.tsx al montar
  _initialize: () => Promise<void>;
}

// ─── Valores iniciales ────────────────────────────────────────────────────
// Antes de que _initialize() cargue las preferencias guardadas.
const INITIAL_STATE = {
  theme: 'system' as Theme,
  resolvedTheme: 'light' as ResolvedTheme,
  language: 'system' as Language,
  resolvedLanguage: 'en' as ResolvedLanguage,
};

// ─── Implementación ───────────────────────────────────────────────────────

export const useAppStore = create<AppStore>((set, get) => ({
  ...INITIAL_STATE,

  setTheme: async (theme) => {
    set({ theme });
    // Persistir en disco mediante tauri-plugin-store
    const store = new Store('markify-prefs.json');
    await store.set('theme', theme);
    await store.save();
    // La resolución del tema la hace useSystemTheme — no hacerlo aquí
  },

  setLanguage: async (lang) => {
    set({ language: lang });
    const store = new Store('markify-prefs.json');
    await store.set('language', lang);
    await store.save();
    // El cambio efectivo en i18next lo hace el componente LanguageToggle
  },

  _setResolvedTheme: (resolvedTheme) => set({ resolvedTheme }),
  _setResolvedLanguage: (resolvedLanguage) => set({ resolvedLanguage }),

  _initialize: async () => {
    try {
      const store = new Store('markify-prefs.json');
      const savedTheme = await store.get<Theme>('theme');
      const savedLang = await store.get<Language>('language');
      set({
        theme: savedTheme ?? 'system',
        language: savedLang ?? 'system',
      });
    } catch {
      // Si falla la lectura del store, usar valores iniciales
      // (primera ejecución o archivo corrupto)
    }
  },
}));
```

---

## 2. `useConversionStore` — Archivos y estado de conversión

```typescript
// src/stores/useConversionStore.ts
import { create } from 'zustand';
import { sanitizeFilename } from '@/lib/sanitizer';
import { formatFileSize, generateZipName } from '@/lib/formatters';
import { getExtension, getFileCategory, isSupportedExtension } from '@/lib/fileUtils';
import { tauriCommands } from '@/lib/tauri';
import type {
  AppState,
  ConversionFile,
  ConversionSummary,
  ConversionProgressEvent,
  ModelDownloadProgressEvent,
  SupportedExtension,
  MAX_FILE_SIZE_BYTES,
  MAX_TOTAL_BATCH_SIZE_BYTES,
  MAX_FILES_PER_BATCH,
} from '@/types';
import { MAX_FILE_SIZE_BYTES, MAX_TOTAL_BATCH_SIZE_BYTES, MAX_FILES_PER_BATCH } from '@/types';

// ─── Tipos de error de validación ─────────────────────────────────────────

export type FileValidationError =
  | { type: 'unsupported'; filename: string; ext: string }
  | { type: 'too_large'; filename: string; sizeBytes: number }
  | { type: 'batch_too_large' }
  | { type: 'too_many_files'; current: number; attempted: number }
  | { type: 'duplicate'; filename: string };

// ─── Interfaz pública ─────────────────────────────────────────────────────

interface ConversionStore {
  // ── Estado ────────────────────────────────────────────────────────────────
  appState: AppState;
  files: ConversionFile[];
  isCancelling: boolean;
  whisperModelAvailable: boolean;
  whisperModelDownloading: boolean;
  whisperModelDownloadProgress: number; // 0-100
  whisperModelDownloadedMB: number;
  whisperModelTotalMB: number;
  validationErrors: FileValidationError[]; // errores del último addFiles()

  // ── Computed (getters — recalculados en cada acceso) ──────────────────────
  readonly summary: ConversionSummary;
  readonly hasAudioFiles: boolean;
  readonly completedFiles: ConversionFile[];
  readonly failedFiles: ConversionFile[];
  readonly pendingFiles: ConversionFile[];
  readonly allCompleted: boolean; // true cuando no quedan pending ni processing
  readonly totalBatchSizeBytes: number;

  // ── Acciones de archivos ──────────────────────────────────────────────────
  addFiles: (rawFiles: File[]) => void;
  // Valida cada archivo, crea ConversionFile[], actualiza validationErrors.
  // No lanza excepciones — los errores se almacenan en validationErrors.

  removeFile: (id: string) => void;
  // Elimina el archivo con ese id. Si la lista queda vacía → appState = 'empty'.

  clearAllFiles: () => void;
  // Vacía la lista. appState → 'empty'.

  clearValidationErrors: () => void;
  // Limpiar errores después de mostrarlos al usuario.

  // ── Acciones de conversión ────────────────────────────────────────────────
  startConversion: (lang: ResolvedLanguage) => Promise<void>;
  // Precondición: appState === 'files-ready' y files.length > 0
  // 1. appState → 'processing'
  // 2. Todos los files → status: 'pending', progress: 0
  // 3. invoke('start_conversion', { files: [...], lang })

  cancelConversion: () => Promise<void>;
  // Precondición: appState === 'processing'
  // 1. isCancelling → true
  // 2. invoke('cancel_conversion')
  // El store vuelve a 'files-ready' cuando llega el evento 'conversion:cancelled'

  retryFailed: (lang: ResolvedLanguage) => Promise<void>;
  // Precondición: appState === 'results' y failedFiles.length > 0
  // 1. Solo los archivos con status === 'error' vuelven a status: 'pending', progress: 0
  // 2. appState → 'processing'
  // 3. invoke('start_conversion') solo con los archivos fallidos

  // ── Acciones de modelo Whisper ────────────────────────────────────────────
  checkWhisperModel: () => Promise<void>;
  // Llama invoke('check_whisper_model'), actualiza whisperModelAvailable.

  startModelDownload: () => Promise<void>;
  // Llama invoke('download_whisper_model'), whisperModelDownloading → true.

  // ── Acciones internas (llamar solo desde useTauriEvents) ──────────────────
  _handleFileUpdate: (event: ConversionProgressEvent) => void;
  _handleModelDownloadProgress: (event: ModelDownloadProgressEvent) => void;
  _handleModelDownloadComplete: () => void;
  _handleConversionComplete: () => void;
  _handleConversionCancelled: () => void;

  // ── Reset ─────────────────────────────────────────────────────────────────
  resetToEmpty: () => void;
  // Vuelve al estado inicial limpio (conserva el estado del modelo Whisper). Llamar al pulsar "Nueva conversión".
}

// ─── Estado inicial ───────────────────────────────────────────────────────

const INITIAL_CONVERSION_STATE = {
  appState: 'empty' as AppState,
  files: [] as ConversionFile[],
  isCancelling: false,
  whisperModelAvailable: false,
  whisperModelDownloading: false,
  whisperModelDownloadProgress: 0,
  whisperModelDownloadedMB: 0,
  whisperModelTotalMB: 145, // WHISPER_MODEL_SIZE_MB
  validationErrors: [] as FileValidationError[],
};

// ─── Implementación ───────────────────────────────────────────────────────

export const useConversionStore = create<ConversionStore>((set, get) => ({
  ...INITIAL_CONVERSION_STATE,

  // ── Computed ─────────────────────────────────────────────────────────────

  get summary(): ConversionSummary {
    const { files } = get();
    return {
      total:     files.length,
      completed: files.filter(f => f.status === 'completed').length,
      failed:    files.filter(f => f.status === 'error').length,
      pending:   files.filter(f => f.status === 'pending' || f.status === 'processing').length,
    };
  },

  get hasAudioFiles(): boolean {
    return get().files.some(f => f.category === 'audio');
  },

  get completedFiles(): ConversionFile[] {
    return get().files.filter(f => f.status === 'completed');
  },

  get failedFiles(): ConversionFile[] {
    return get().files.filter(f => f.status === 'error');
  },

  get pendingFiles(): ConversionFile[] {
    return get().files.filter(f => f.status === 'pending');
  },

  get allCompleted(): boolean {
    const { files } = get();
    return files.length > 0 &&
      files.every(f => f.status === 'completed' || f.status === 'error');
  },

  get totalBatchSizeBytes(): number {
    return get().files.reduce((sum, f) => sum + f.sizeBytes, 0);
  },

  // ── addFiles ──────────────────────────────────────────────────────────────

  addFiles: (rawFiles) => {
    const { files } = get();
    const errors: FileValidationError[] = [];
    const toAdd: ConversionFile[] = [];

    // Verificar límite de cantidad
    if (files.length + rawFiles.length > MAX_FILES_PER_BATCH) {
      errors.push({
        type: 'too_many_files',
        current: files.length,
        attempted: rawFiles.length,
      });
      set({ validationErrors: errors });
      return;
    }

    let runningBatchSize = get().totalBatchSizeBytes;

    for (const rawFile of rawFiles) {
      const ext = getExtension(rawFile.name);

      // Extensión no soportada
      if (!isSupportedExtension(ext)) {
        errors.push({ type: 'unsupported', filename: rawFile.name, ext });
        continue;
      }

      // Archivo demasiado grande
      if (rawFile.size > MAX_FILE_SIZE_BYTES) {
        errors.push({ type: 'too_large', filename: rawFile.name, sizeBytes: rawFile.size });
        continue;
      }

      // Batch total demasiado grande
      if (runningBatchSize + rawFile.size > MAX_TOTAL_BATCH_SIZE_BYTES) {
        errors.push({ type: 'batch_too_large' });
        break; // No seguir procesando
      }

      // Duplicado (mismo path)
      const isDuplicate = files.some(f => f.path === (rawFile as any).path) ||
                          toAdd.some(f => f.path === (rawFile as any).path);
      if (isDuplicate) {
        errors.push({ type: 'duplicate', filename: rawFile.name });
        continue;
      }

      const category = getFileCategory(ext)!;
      const newFile: ConversionFile = {
        id:            crypto.randomUUID(),
        originalName:  rawFile.name,
        sanitizedName: sanitizeFilename(rawFile.name),
        path:          (rawFile as any).path ?? rawFile.name, // Tauri provee .path
        sizeBytes:     rawFile.size,
        formattedSize: formatFileSize(rawFile.size),
        category,
        extension: ext,
        status: 'pending',
        progress: 0,
      };

      toAdd.push(newFile);
      runningBatchSize += rawFile.size;
    }

    set(state => ({
      files: [...state.files, ...toAdd],
      appState: state.files.length + toAdd.length > 0 ? 'files-ready' : state.appState,
      validationErrors: errors,
    }));
  },

  // ── removeFile ────────────────────────────────────────────────────────────

  removeFile: (id) => {
    set(state => {
      const newFiles = state.files.filter(f => f.id !== id);
      return {
        files: newFiles,
        appState: newFiles.length === 0 ? 'empty' : state.appState,
      };
    });
  },

  // ── clearAllFiles ─────────────────────────────────────────────────────────

  clearAllFiles: () => {
    set({ files: [], appState: 'empty', validationErrors: [] });
  },

  clearValidationErrors: () => set({ validationErrors: [] }),

  // ── startConversion ───────────────────────────────────────────────────────

  startConversion: async (lang) => {
    const { files } = get();
    if (files.length === 0) return;

    // Resetear todos los archivos a pending
    set(state => ({
      appState: 'processing',
      isCancelling: false,
      files: state.files.map(f => ({
        ...f,
        status: 'pending' as const,
        progress: 0,
        errorMessage: undefined,
        markdownContent: undefined,
      })),
    }));

    await tauriCommands.startConversion({
      files: files.map(f => ({ id: f.id, path: f.path, category: f.category })),
      lang,
    });
  },

  // ── cancelConversion ──────────────────────────────────────────────────────

  cancelConversion: async () => {
    set({ isCancelling: true });
    await tauriCommands.cancelConversion();
    // El store vuelve a 'files-ready' en _handleConversionCancelled
  },

  // ── retryFailed ───────────────────────────────────────────────────────────

  retryFailed: async (lang) => {
    const { files } = get();
    const failed = files.filter(f => f.status === 'error');
    if (failed.length === 0) return;

    set(state => ({
      appState: 'processing',
      isCancelling: false,
      files: state.files.map(f =>
        f.status === 'error'
          ? { ...f, status: 'pending' as const, progress: 0, errorMessage: undefined }
          : f
      ),
    }));

    await tauriCommands.startConversion({
      files: failed.map(f => ({ id: f.id, path: f.path, category: f.category })),
      lang,
    });
  },

  // ── checkWhisperModel ─────────────────────────────────────────────────────

  checkWhisperModel: async () => {
    const available = await tauriCommands.checkWhisperModel();
    set({ whisperModelAvailable: available });
  },

  startModelDownload: async () => {
    set({ whisperModelDownloading: true, whisperModelDownloadProgress: 0 });
    await tauriCommands.downloadWhisperModel();
  },

  // ── Handlers internos ─────────────────────────────────────────────────────

  _handleFileUpdate: (event) => {
    set(state => ({
      files: state.files.map(f =>
        f.id === event.fileId
          ? {
              ...f,
              status: event.status,
              progress: event.progress,
              errorMessage: event.errorMessage,
              markdownContent: event.markdownContent,
            }
          : f
      ),
    }));
  },

  _handleModelDownloadProgress: (event) => {
    set({
      whisperModelDownloadProgress: event.percent,
      whisperModelDownloadedMB: event.downloadedMB,
      whisperModelTotalMB: event.totalMB,
    });
  },

  _handleModelDownloadComplete: () => {
    set({
      whisperModelAvailable: true,
      whisperModelDownloading: false,
      whisperModelDownloadProgress: 100,
    });
  },

  _handleConversionComplete: () => {
    set({ appState: 'results', isCancelling: false });
  },

  _handleConversionCancelled: () => {
    // Al cancelar, resetear todos los archivos pending/processing a pending
    // para que el usuario pueda intentar de nuevo con la misma lista
    set(state => ({
      appState: 'files-ready',
      isCancelling: false,
      files: state.files.map(f =>
        f.status === 'pending' || f.status === 'processing'
          ? { ...f, status: 'pending' as const, progress: 0 }
          : f
      ),
    }));
  },

  // ── resetToEmpty ──────────────────────────────────────────────────────────

  resetToEmpty: () => {
    // El modelo Whisper es del equipo, no de la conversión: conservar su estado
    // (si no, "Nueva conversión" volvería a pedir la descarga).
    const {
      whisperModelAvailable, whisperModelDownloading, whisperModelDownloadProgress,
      whisperModelDownloadedMB, whisperModelTotalMB,
    } = get();
    set({
      ...INITIAL_CONVERSION_STATE,
      whisperModelAvailable, whisperModelDownloading, whisperModelDownloadProgress,
      whisperModelDownloadedMB, whisperModelTotalMB,
    });
  },
}));
```

---

## 3. `usePreviewStore` — Selección de archivo en preview

```typescript
// src/stores/usePreviewStore.ts
import { create } from 'zustand';
import type { PreviewViewMode } from '@/types';

interface PreviewStore {
  selectedFileId: string | null;
  viewMode: PreviewViewMode;

  // Selecciona un archivo para mostrar en el preview
  selectFile: (id: string) => void;

  // Alterna entre 'rendered' y 'raw'
  toggleViewMode: () => void;

  // Resetear — llamar junto con useConversionStore.resetToEmpty()
  reset: () => void;
}

export const usePreviewStore = create<PreviewStore>((set, get) => ({
  selectedFileId: null,
  viewMode: 'rendered',

  selectFile: (id) => set({ selectedFileId: id }),

  toggleViewMode: () => set(state => ({
    viewMode: state.viewMode === 'rendered' ? 'raw' : 'rendered',
  })),

  reset: () => set({ selectedFileId: null, viewMode: 'rendered' }),
}));
```

---

## 4. Hook de suscripción a eventos Tauri (`src/hooks/useTauriEvents.ts`)

```typescript
// Este hook conecta los eventos Tauri con las acciones internas de los stores.
// Montar UNA VEZ en App.tsx. Gestiona suscripción y desuscripción.

import { useEffect } from 'react';
import { tauriEvents } from '@/lib/tauri';
import { useConversionStore } from '@/stores/useConversionStore';

export function useTauriEvents() {
  const store = useConversionStore;

  useEffect(() => {
    // Registrar todos los listeners
    const unlisteners: Promise<() => void>[] = [
      tauriEvents.onFileUpdate(event => {
        useConversionStore.getState()._handleFileUpdate(event);
      }),

      tauriEvents.onModelDownloadProgress(event => {
        useConversionStore.getState()._handleModelDownloadProgress(event);
      }),

      tauriEvents.onModelDownloadComplete(() => {
        useConversionStore.getState()._handleModelDownloadComplete();
      }),

      tauriEvents.onConversionComplete(() => {
        useConversionStore.getState()._handleConversionComplete();
      }),

      tauriEvents.onConversionCancelled(() => {
        useConversionStore.getState()._handleConversionCancelled();
      }),

      tauriEvents.onModelDownloadError((message) => {
        // Aquí podría mostrarse un toast de error global
        useConversionStore.setState({
          whisperModelDownloading: false,
          whisperModelDownloadProgress: 0,
        });
        console.error('[Markify] Model download error:', message);
      }),
    ];

    // Cleanup — desregistrar al desmontar
    return () => {
      unlisteners.forEach(p => p.then(fn => fn()));
    };
  }, []);
}
```

---

## 5. Reglas de transición de `appState`

```
┌─────────────────────────────────────────────────────────────────┐
│              MÁQUINA DE ESTADOS DE appState                     │
│                                                                 │
│   empty ──── addFiles() con archivos válidos ────→ files-ready  │
│                                                                 │
│   files-ready ──── removeFile() [last] ──────────→ empty        │
│   files-ready ──── clearAllFiles() ──────────────→ empty        │
│   files-ready ──── startConversion() ────────────→ processing   │
│                                                                 │
│   processing ──── _handleConversionCancelled() ──→ files-ready  │
│   processing ──── _handleConversionComplete() ───→ results      │
│                                                                 │
│   results ──── resetToEmpty() ───────────────────→ empty        │
│   results ──── retryFailed() ────────────────────→ processing   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Invariantes (nunca violar):**
- En `processing`, no se pueden añadir ni eliminar archivos.
- En `results`, no se pueden añadir archivos.
- `resetToEmpty()` siempre lleva a `empty` independientemente del estado actual.
- El botón "Convertir" solo está activo cuando `appState === 'files-ready'`.

---

## 6. Selectors recomendados para componentes

```typescript
// Importar así en componentes — solo suscribirse a lo necesario

// ── En Header ────────────────────────────────────────────────────────────
const theme    = useAppStore(s => s.theme);
const setTheme = useAppStore(s => s.setTheme);

// ── En FileList ──────────────────────────────────────────────────────────
const files        = useConversionStore(s => s.files);
const appState     = useConversionStore(s => s.appState);
const removeFile   = useConversionStore(s => s.removeFile);
const clearAll     = useConversionStore(s => s.clearAllFiles);

// ── En ProcessingView ─────────────────────────────────────────────────────
const files      = useConversionStore(s => s.files);
const summary    = useConversionStore(s => s.summary);
const cancel     = useConversionStore(s => s.cancelConversion);
const cancelling = useConversionStore(s => s.isCancelling);

// ── En ResultsView ────────────────────────────────────────────────────────
const completedFiles = useConversionStore(s => s.completedFiles);
const failedFiles    = useConversionStore(s => s.failedFiles);
const summary        = useConversionStore(s => s.summary);

// ── En PreviewPanel ───────────────────────────────────────────────────────
const selectedId   = usePreviewStore(s => s.selectedFileId);
const viewMode     = usePreviewStore(s => s.viewMode);
const toggleMode   = usePreviewStore(s => s.toggleViewMode);
const files        = useConversionStore(s => s.files);
const selectedFile = files.find(f => f.id === selectedId);
const content      = selectedFile?.markdownContent ?? null;
```
