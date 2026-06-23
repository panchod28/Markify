import { useEffect } from 'react';
import { getCurrentWebview } from '@tauri-apps/api/webview';
import { useAppStore } from '@/stores/useAppStore';
import { useConversionStore } from '@/stores/useConversionStore';
import { useTauriEvents } from '@/hooks/useTauriEvents';
import { useSystemTheme } from '@/hooks/useSystemTheme';
import { Header } from '@/components/layout/Header';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const resolvedTheme = useAppStore(s => s.resolvedTheme);

  useTauriEvents();
  useSystemTheme();

  useEffect(() => {
    useAppStore.getState()._initialize();
    useConversionStore.getState().checkWhisperModel();
  }, []);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    let mounted = true;
    getCurrentWebview().onDragDropEvent((event) => {
      if (event.payload.type === 'drop') {
        useConversionStore.getState().addFilePaths(event.payload.paths);
      }
    }).then(fn => {
      if (mounted) {
        unlisten = fn;
      } else {
        fn(); // ya desmontado, limpiar inmediatamente
      }
    });
    return () => {
      mounted = false;
      unlisten?.();
    };
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolvedTheme);
  }, [resolvedTheme]);

  return (
    <div className="flex flex-col h-screen bg-bg overflow-hidden">
      <Header />
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
