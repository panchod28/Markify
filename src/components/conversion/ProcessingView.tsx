import { useTranslation } from 'react-i18next';
import { ScrollArea } from '@/components/ui/scroll-area';
import { GlobalProgress } from './GlobalProgress';
import { ProcessingFileItem } from './ProcessingFileItem';
import type { ConversionFile, ConversionSummary } from '@/types';

interface ProcessingViewProps {
  files: ConversionFile[];
  summary: ConversionSummary;
  isCancelling: boolean;
  onCancel: () => void;
}

export function ProcessingView({ files, summary, isCancelling, onCancel }: ProcessingViewProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col h-full">
      <GlobalProgress summary={summary} />

      <ScrollArea className="flex-1">
        {files.map(file => (
          <ProcessingFileItem key={file.id} file={file} />
        ))}
      </ScrollArea>

      <div className="flex justify-end px-4 py-3 border-t border-border">
        <button
          onClick={onCancel}
          disabled={isCancelling}
          className="h-11 px-5 text-sm font-medium text-error border border-error rounded-md hover:bg-error-subtle disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-fast"
        >
          {isCancelling ? t('processing.cancelling') : t('processing.cancel')}
        </button>
      </div>
    </div>
  );
}
