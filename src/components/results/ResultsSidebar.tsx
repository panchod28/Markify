import { useTranslation } from 'react-i18next';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckCircle } from 'lucide-react';
import { ResultFileItem } from './ResultFileItem';
import { cn } from '@/lib/cn';
import type { ConversionFile, ConversionSummary } from '@/types';

interface ResultsSidebarProps {
  files: ConversionFile[];
  summary: ConversionSummary;
  selectedFileId: string | null;
  onSelectFile: (id: string) => void;
  className?: string;
}

export function ResultsSidebar({
  files,
  summary,
  selectedFileId,
  onSelectFile,
  className,
}: ResultsSidebarProps) {
  const { t } = useTranslation();

  return (
    <div className={cn('flex flex-col min-w-[220px] max-w-[300px] w-[25%] flex-shrink-0 border-r border-border', className)}>
      <div className="px-4 py-4 border-b border-border">
        <div className="flex items-center gap-2 mb-1">
          <CheckCircle size={20} className="text-success" />
          <span className="text-base font-semibold text-text-primary">
            {t('results.successAll', { count: summary.completed })}
          </span>
        </div>
        {summary.failed > 0 && (
          <p className="text-sm text-error">
            {t('results.failedCount', { count: summary.failed })}
          </p>
        )}
      </div>

      <ScrollArea className="flex-1">
        {files.map(file => (
          <ResultFileItem
            key={file.id}
            file={file}
            isSelected={file.id === selectedFileId}
            onClick={() => file.status === 'completed' && onSelectFile(file.id)}
          />
        ))}
      </ScrollArea>
    </div>
  );
}
