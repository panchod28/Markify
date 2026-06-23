import { useTranslation } from 'react-i18next';
import { Brain } from 'lucide-react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { ProgressBar } from '@/components/conversion/ProgressBar';

interface WhisperModelModalProps {
  open: boolean;
  isDownloading: boolean;
  downloadProgress: number;
  downloadedMB: number;
  totalMB: number;
  downloadError: string | null;
  onConfirm: () => void;
  onDismiss: () => void;
}

export function WhisperModelModal({
  open,
  isDownloading,
  downloadProgress,
  downloadedMB,
  totalMB,
  downloadError,
  onConfirm,
  onDismiss,
}: WhisperModelModalProps) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={isDownloading ? undefined : onDismiss}>
      <DialogContent className="max-w-[400px]">
        <div className="flex flex-col items-center gap-4 py-4">
          <Brain size={48} className="text-accent" />

          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">{t('whisperModal.title')}</h2>
            <p className="text-sm text-text-secondary">
              {t('whisperModal.description')}
            </p>
          </div>

          {downloadError && (
            <p className="text-sm text-error text-center">{downloadError}</p>
          )}

          {isDownloading && (
            <div className="w-full">
              <ProgressBar progress={downloadProgress} status="processing" />
              <p className="text-xs text-text-secondary text-center mt-2">
                {t('whisperModal.progress', {
                  percent: downloadProgress,
                  downloaded: downloadedMB.toFixed(1),
                  total: totalMB.toFixed(1),
                })}
              </p>
            </div>
          )}

          {!isDownloading && (
            <div className="flex gap-2 w-full">
              <button
                onClick={onDismiss}
                className="flex-1 h-10 px-4 text-sm font-medium border border-border rounded-md hover:bg-surface-secondary transition-colors"
              >
                {t('whisperModal.cancel')}
              </button>
              <button
                onClick={onConfirm}
                className="flex-1 h-10 px-4 bg-accent hover:bg-accent-hover text-text-onaccent text-sm font-semibold rounded-md transition-colors"
              >
                {t('whisperModal.downloadAndContinue')}
              </button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
