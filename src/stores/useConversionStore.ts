import { create } from 'zustand';
import { stat } from '@tauri-apps/plugin-fs';
import { sanitizeFilename } from '@/lib/sanitizer';
import { formatFileSize } from '@/lib/formatters';
import { getExtension, getFileCategory, isLegacyExtension, isSupportedExtension } from '@/lib/fileUtils';
import { tauriCommands } from '@/lib/tauri';
import type {
  AppState,
  ConversionFile,
  ConversionProgressEvent,
  ModelDownloadProgressEvent,
  ResolvedLanguage,
} from '@/types';
import { MAX_FILE_SIZE_BYTES, MAX_TOTAL_BATCH_SIZE_BYTES, MAX_FILES_PER_BATCH } from '@/types';

export type FileValidationError =
  | { type: 'unsupported'; filename: string; ext: string }
  | { type: 'legacy_format'; filename: string; ext: string }
  | { type: 'too_large'; filename: string; sizeBytes: number }
  | { type: 'batch_too_large' }
  | { type: 'too_many_files'; current: number; attempted: number }
  | { type: 'duplicate'; filename: string };

interface ConversionStore {
  appState: AppState;
  files: ConversionFile[];
  isCancelling: boolean;
  whisperModelAvailable: boolean;
  whisperModelDownloading: boolean;
  whisperModelDownloadProgress: number;
  whisperModelDownloadedMB: number;
  whisperModelTotalMB: number;
  validationErrors: FileValidationError[];


  addFiles: (rawFiles: File[]) => void;
  addFilePaths: (paths: string[]) => Promise<void>;
  removeFile: (id: string) => void;
  clearAllFiles: () => void;
  clearValidationErrors: () => void;

  startConversion: (lang: ResolvedLanguage) => Promise<void>;
  cancelConversion: () => Promise<void>;
  retryFailed: (lang: ResolvedLanguage) => Promise<void>;

  checkWhisperModel: () => Promise<void>;
  startModelDownload: () => Promise<void>;

  _handleFileUpdate: (event: ConversionProgressEvent) => void;
  _handleModelDownloadProgress: (event: ModelDownloadProgressEvent) => void;
  _handleModelDownloadComplete: () => void;
  _handleConversionComplete: () => void;
  _handleConversionCancelled: () => void;

  resetToEmpty: () => void;
}

const INITIAL_CONVERSION_STATE = {
  appState: 'empty' as AppState,
  files: [] as ConversionFile[],
  isCancelling: false,
  whisperModelAvailable: false,
  whisperModelDownloading: false,
  whisperModelDownloadProgress: 0,
  whisperModelDownloadedMB: 0,
  whisperModelTotalMB: 145,
  validationErrors: [] as FileValidationError[],
};

export const useConversionStore = create<ConversionStore>((set, get) => ({
  ...INITIAL_CONVERSION_STATE,


  // ── addFiles ──────────────────────────────────────────────────────────────

  addFiles: (rawFiles) => {
    const { files } = get();
    const errors: FileValidationError[] = [];
    const toAdd: ConversionFile[] = [];

    if (files.length + rawFiles.length > MAX_FILES_PER_BATCH) {
      errors.push({
        type: 'too_many_files',
        current: files.length,
        attempted: rawFiles.length,
      });
      set({ validationErrors: errors });
      return;
    }

    let runningBatchSize = get().files.reduce((sum, f) => sum + f.sizeBytes, 0);

    for (const rawFile of rawFiles) {
      const ext = getExtension(rawFile.name);

      if (isLegacyExtension(ext)) {
        errors.push({ type: 'legacy_format', filename: rawFile.name, ext });
        continue;
      }

      if (!isSupportedExtension(ext)) {
        errors.push({ type: 'unsupported', filename: rawFile.name, ext });
        continue;
      }

      if (rawFile.size > MAX_FILE_SIZE_BYTES) {
        errors.push({ type: 'too_large', filename: rawFile.name, sizeBytes: rawFile.size });
        continue;
      }

      if (runningBatchSize + rawFile.size > MAX_TOTAL_BATCH_SIZE_BYTES) {
        errors.push({ type: 'batch_too_large' });
        break;
      }

      const filePath = (rawFile as unknown as { path?: string }).path ?? rawFile.name;
      const isDuplicate = files.some(f => f.path === filePath) ||
                          toAdd.some(f => f.path === filePath);
      if (isDuplicate) {
        errors.push({ type: 'duplicate', filename: rawFile.name });
        continue;
      }

      const category = getFileCategory(ext)!;
      const newFile: ConversionFile = {
        id:            crypto.randomUUID(),
        originalName:  rawFile.name,
        sanitizedName: sanitizeFilename(rawFile.name),
        path:          filePath,
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

  // ── addFilePaths ───────────────────────────────────────────────────────────

  addFilePaths: async (paths) => {
    const { files } = get();
    const errors: FileValidationError[] = [];
    const toAdd: ConversionFile[] = [];

    if (files.length + paths.length > MAX_FILES_PER_BATCH) {
      errors.push({
        type: 'too_many_files',
        current: files.length,
        attempted: paths.length,
      });
      set({ validationErrors: errors });
      return;
    }

    let runningBatchSize = get().files.reduce((sum, f) => sum + f.sizeBytes, 0);

    for (const filePath of paths) {
      const separator = filePath.includes('\\') ? '\\' : '/';
      const originalName = filePath.split(separator).pop()!;
      const ext = getExtension(originalName);

      if (isLegacyExtension(ext)) {
        errors.push({ type: 'legacy_format', filename: originalName, ext });
        continue;
      }

      if (!isSupportedExtension(ext)) {
        errors.push({ type: 'unsupported', filename: originalName, ext });
        continue;
      }

      let sizeBytes: number;
      try {
        const info = await stat(filePath);
        sizeBytes = info.size;
      } catch {
        sizeBytes = 0;
      }

      if (sizeBytes > MAX_FILE_SIZE_BYTES) {
        errors.push({ type: 'too_large', filename: originalName, sizeBytes });
        continue;
      }

      if (runningBatchSize + sizeBytes > MAX_TOTAL_BATCH_SIZE_BYTES) {
        errors.push({ type: 'batch_too_large' });
        break;
      }

      const isDuplicate = files.some(f => f.path === filePath) ||
                          toAdd.some(f => f.path === filePath);
      if (isDuplicate) {
        errors.push({ type: 'duplicate', filename: originalName });
        continue;
      }

      const category = getFileCategory(ext)!;
      const newFile: ConversionFile = {
        id:            crypto.randomUUID(),
        originalName,
        sanitizedName: sanitizeFilename(originalName),
        path:          filePath,
        sizeBytes,
        formattedSize: formatFileSize(sizeBytes),
        category,
        extension: ext,
        status: 'pending',
        progress: 0,
      };

      toAdd.push(newFile);
      runningBatchSize += sizeBytes;
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

    set(state => ({
      appState: 'processing',
      isCancelling: false,
      files: state.files.map(f => ({
        ...f,
        status: 'pending' as const,
        progress: 0,
        errorMessage: undefined,
        markdownContent: undefined,
        warnings: undefined,
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
          ? { ...f, status: 'pending' as const, progress: 0, errorMessage: undefined, warnings: undefined }
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
    try {
      const available = await tauriCommands.checkWhisperModel();
      set({ whisperModelAvailable: available });
    } catch (err) {
      // Sidecar aún no responde (primer arranque lento): conservar el estado previo.
      console.error('[Markify] checkWhisperModel failed:', err);
    }
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
              warnings: event.warnings,
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
    // El modelo Whisper es del equipo, no de la conversión: conservar su estado (si no, "Nueva
    // conversión" lo daría por ausente y volvería a pedir la descarga).
    const {
      whisperModelAvailable,
      whisperModelDownloading,
      whisperModelDownloadProgress,
      whisperModelDownloadedMB,
      whisperModelTotalMB,
    } = get();
    set({
      ...INITIAL_CONVERSION_STATE,
      whisperModelAvailable,
      whisperModelDownloading,
      whisperModelDownloadProgress,
      whisperModelDownloadedMB,
      whisperModelTotalMB,
    });
  },
}));
