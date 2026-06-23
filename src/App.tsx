import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import { AppShell } from '@/components/layout/AppShell';
import { DropZone } from '@/components/dropzone/DropZone';
import { FileList } from '@/components/files/FileList';
import { ProcessingView } from '@/components/conversion/ProcessingView';
import { ResultsView } from '@/components/results/ResultsView';
import { WhisperModelModal } from '@/components/modals/WhisperModelModal';
import { ConfirmDialog } from '@/components/modals/ConfirmDialog';
import { ValidationErrorToast } from '@/components/ui/ValidationErrorToast';
import { useConversionStore } from '@/stores/useConversionStore';
import { usePreviewStore } from '@/stores/usePreviewStore';
import { useAppStore } from '@/stores/useAppStore';
import { tauriCommands } from '@/lib/tauri';
import type { ResolvedLanguage } from '@/types';
import { generateZipName } from '@/lib/formatters';

export default function App() {
  const { t } = useTranslation();
  const appState = useConversionStore(s => s.appState);
  const files = useConversionStore(s => s.files);
  const isCancelling = useConversionStore(s => s.isCancelling);

  const summary = useMemo(() => ({
    total:     files.length,
    completed: files.filter(f => f.status === 'completed').length,
    failed:    files.filter(f => f.status === 'error').length,
    pending:   files.filter(f => f.status === 'pending' || f.status === 'processing').length,
  }), [files]);

  const completedFiles = useMemo(
    () => files.filter(f => f.status === 'completed'),
    [files]
  );
  const whisperModelAvailable = useConversionStore(s => s.whisperModelAvailable);
  const whisperModelDownloading = useConversionStore(s => s.whisperModelDownloading);
  const whisperModelDownloadProgress = useConversionStore(s => s.whisperModelDownloadProgress);
  const whisperModelDownloadedMB = useConversionStore(s => s.whisperModelDownloadedMB);
  const whisperModelTotalMB = useConversionStore(s => s.whisperModelTotalMB);
  const validationErrors = useConversionStore(s => s.validationErrors);

  const selectedFileId = usePreviewStore(s => s.selectedFileId);
  const viewMode = usePreviewStore(s => s.viewMode);
  const resolvedLanguage = useAppStore(s => s.resolvedLanguage);

  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [showWhisperModal, setShowWhisperModal] = useState(false);
  const [whisperModalDismissed, setWhisperModalDismissed] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [savedPath, setSavedPath] = useState<string | null>(null);

  // Whisper model check — show modal only if audio files exist and model not available
  const handleConvert = useCallback(() => {
    const hasAudio = files.some(f => f.category === 'audio');
    if (hasAudio && !whisperModelAvailable && !whisperModalDismissed) {
      setShowWhisperModal(true);
      return;
    }
    const lang: ResolvedLanguage = resolvedLanguage;
    useConversionStore.getState().startConversion(lang);
    setSavedPath(null);
  }, [files, whisperModelAvailable, whisperModalDismissed, resolvedLanguage]);


  const handleSave = useCallback(async () => {
    if (summary.completed === 1) {
      const file = completedFiles[0];
      if (file) {
        const path = await tauriCommands.saveMarkdown(file.markdownContent ?? '', file.sanitizedName);
        setSavedPath(path);
      }
    } else {
      const payload = {
        files: completedFiles.map(f => ({ name: f.sanitizedName, content: f.markdownContent ?? '' })),
        suggestedName: generateZipName(),
      };
      const path = await tauriCommands.saveZip(payload);
      setSavedPath(path);
    }
  }, [summary.completed, completedFiles]);

  const handleOpenInFolder = useCallback(async () => {
    if (savedPath) {
      await tauriCommands.openInFolder(savedPath);
    }
  }, [savedPath]);

  const handleRetryFailed = useCallback(() => {
    const lang: ResolvedLanguage = resolvedLanguage;
    useConversionStore.getState().retryFailed(lang);
    setSavedPath(null);
  }, [resolvedLanguage]);

  const handleNewConversion = useCallback(() => {
    useConversionStore.getState().resetToEmpty();
    usePreviewStore.getState().reset();
    setSavedPath(null);
  }, []);

  const handleCancelConversion = useCallback(() => {
    setShowCancelConfirm(true);
  }, []);

  const confirmCancel = useCallback(() => {
    setShowCancelConfirm(false);
    useConversionStore.getState().cancelConversion();
  }, []);

  const handleWhisperConfirm = useCallback(async () => {
    setDownloadError(null);
    try {
      await useConversionStore.getState().startModelDownload();
      setShowWhisperModal(false);
      const lang: ResolvedLanguage = resolvedLanguage;
      useConversionStore.getState().startConversion(lang);
      setSavedPath(null);
    } catch {
      setDownloadError(t('whisperModal.retry'));
    }
  }, [resolvedLanguage]);

  return (
    <AppShell>
      <AnimatePresence mode="wait">
        {appState === 'empty' && (
          <motion.div
            key="empty"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="flex items-center justify-center h-full p-8"
          >
            <DropZone />
          </motion.div>
        )}

        {appState === 'files-ready' && (
          <motion.div
            key="files-ready"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="h-full"
          >
            <FileList
              files={files}
              onRemove={id => useConversionStore.getState().removeFile(id)}
              onClearAll={() => useConversionStore.getState().clearAllFiles()}

              onConvert={handleConvert}
              isConvertDisabled={files.length === 0}
            />
          </motion.div>
        )}

        {appState === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="h-full"
          >
            <ProcessingView
              files={files}
              summary={summary}
              isCancelling={isCancelling}
              onCancel={handleCancelConversion}
            />
          </motion.div>
        )}

        {appState === 'results' && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="h-full"
          >
            <ResultsView
              files={files}
              summary={summary}
              selectedFileId={selectedFileId}
              onSelectFile={id => usePreviewStore.getState().selectFile(id)}
              onSave={handleSave}
              onRetryFailed={handleRetryFailed}
              onNewConversion={handleNewConversion}
              viewMode={viewMode}
              onToggleViewMode={() => usePreviewStore.getState().toggleViewMode()}
              savedPath={savedPath}
              onOpenInFolder={handleOpenInFolder}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <WhisperModelModal
        open={showWhisperModal}
        isDownloading={whisperModelDownloading}
        downloadProgress={whisperModelDownloadProgress}
        downloadedMB={whisperModelDownloadedMB}
        totalMB={whisperModelTotalMB}
        downloadError={downloadError}
        onConfirm={handleWhisperConfirm}
        onDismiss={() => {
          setShowWhisperModal(false);
          setWhisperModalDismissed(true);
        }}
      />

      <ConfirmDialog
        open={showCancelConfirm}
        title={t('confirmDialog.cancelConversion.title')}
        description={t('confirmDialog.cancelConversion.description')}
        confirmLabel={t('confirmDialog.cancelConversion.confirm')}
        dismissLabel={t('confirmDialog.cancelConversion.dismiss')}
        variant="destructive"
        onConfirm={confirmCancel}
        onDismiss={() => setShowCancelConfirm(false)}
      />

      <ValidationErrorToast
        errors={validationErrors}
        onDismiss={() => useConversionStore.getState().clearValidationErrors()}
      />
    </AppShell>
  );
}
