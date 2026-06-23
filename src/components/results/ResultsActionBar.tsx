import { useTranslation } from 'react-i18next';
import { FolderOpen } from 'lucide-react';
import type { ConversionSummary } from '@/types';

interface ResultsActionBarProps {
  summary: ConversionSummary;
  savedPath: string | null;
  onSave: () => Promise<void>;
  onRetryFailed: () => void;
  onNewConversion: () => void;
  onOpenInFolder: () => void;
}

export function ResultsActionBar({
  summary,
  savedPath,
  onSave,
  onRetryFailed,
  onNewConversion,
  onOpenInFolder,
}: ResultsActionBarProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-surface">
      <div className="flex items-center gap-2">
        {summary.completed > 0 && !savedPath && (
          <button
            onClick={onSave}
            className="h-9 px-4 bg-accent hover:bg-accent-hover text-text-onaccent text-sm font-semibold rounded-md transition-colors duration-fast"
          >
            {summary.completed === 1 ? t('results.saveMd') : t('results.saveZip')}
          </button>
        )}

        {savedPath && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-secondary truncate max-w-[300px]">
              {t('results.savedAt')} {savedPath}
            </span>
            <button
              onClick={onOpenInFolder}
              className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-accent rounded-md hover:bg-accent-subtle transition-colors"
            >
              <FolderOpen size={14} />
              {t('results.openInFolder')}
            </button>
          </div>
        )}

        {summary.failed > 0 && (
          <button
            onClick={onRetryFailed}
            className="h-9 px-4 text-sm font-medium text-error border border-error rounded-md hover:bg-error-subtle transition-colors duration-fast"
          >
            {t('results.retryFailed')}
          </button>
        )}
      </div>

      <button
        onClick={onNewConversion}
        className="h-9 px-4 text-sm font-medium text-text-secondary rounded-md hover:bg-surface-secondary transition-colors"
      >
        {t('results.newConversion')}
      </button>
    </div>
  );
}
