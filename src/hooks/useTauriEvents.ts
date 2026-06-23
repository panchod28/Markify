import { useEffect } from 'react';
import { tauriEvents } from '@/lib/tauri';
import { useConversionStore } from '@/stores/useConversionStore';

export function useTauriEvents() {
  useEffect(() => {
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
        useConversionStore.setState({
          whisperModelDownloading: false,
          whisperModelDownloadProgress: 0,
        });
        console.error('[Markify] Model download error:', message);
      }),
    ];

    return () => {
      unlisteners.forEach(p => p.then(fn => fn()));
    };
  }, []);
}
