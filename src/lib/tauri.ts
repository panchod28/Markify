import { invoke } from '@tauri-apps/api/core';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import type {
  StartConversionPayload,
  SaveZipPayload,
  ConversionProgressEvent,
  ModelDownloadProgressEvent,
} from '@/types';

// ─── Comandos ─────────────────────────────────────────────────────────────

export const tauriCommands = {
  startConversion: (payload: StartConversionPayload): Promise<void> =>
    invoke('start_conversion', payload as unknown as Record<string, unknown>),

  cancelConversion: (): Promise<void> =>
    invoke('cancel_conversion'),

  saveMarkdown: (content: string, suggestedName: string): Promise<string | null> =>
    invoke('save_markdown', { content, suggestedName }),

  saveZip: (payload: SaveZipPayload): Promise<string | null> =>
    invoke('save_zip', payload as unknown as Record<string, unknown>),

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
