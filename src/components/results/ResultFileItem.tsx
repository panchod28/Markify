import { FileIcon } from '@/components/files/FileIcon';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import type { ConversionFile } from '@/types';

interface ResultFileItemProps {
  file: ConversionFile;
  isSelected: boolean;
  onClick: () => void;
}

function smartTruncate(name: string, maxLength: number = 22): string {
  if (name.length <= maxLength) return name;
  const dotIndex = name.lastIndexOf('.');
  if (dotIndex === -1) return name.slice(0, maxLength - 3) + '...';
  const ext = name.slice(dotIndex);         // e.g. ".xlsx"
  const base = name.slice(0, dotIndex);     // nombre sin extensión
  const charsForBase = maxLength - ext.length - 3; // 3 = "..."
  if (charsForBase <= 0) return name.slice(0, maxLength - 3) + '...';
  return base.slice(0, charsForBase) + '...' + ext;
}

export function ResultFileItem({ file, isSelected, onClick }: ResultFileItemProps) {
  const { t } = useTranslation();
  const isClickable = file.status === 'completed';
  const warnings = file.status === 'completed' ? file.warnings ?? [] : [];
  const warningsTitle = warnings.length
    ? [t('results.warningsTitle'), ...warnings.map(w => `• ${w.message}`)].join('\n')
    : undefined;
  const displayName = smartTruncate(file.originalName, 22);
  const showTooltip = file.originalName.length > 22;

  return (
    <div
      onClick={isClickable ? onClick : undefined}
      title={showTooltip ? file.originalName : undefined}
      className={`
        flex items-center gap-2 px-3 py-2 pr-4
        ${isClickable ? 'cursor-pointer hover:bg-surface-secondary' : ''}
        ${isSelected ? 'bg-accent-subtle border-l-[3px] border-l-accent' : 'border-l-[3px] border-l-transparent'}
        transition-colors duration-[100ms]
      `}
    >
      <div className="flex-shrink-0">
        <FileIcon extension={file.extension} size={20} />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary">
          {displayName}
        </p>
        {file.status === 'error' && file.errorMessage && (
          <p className="text-xs text-error mt-0.5 truncate">{file.errorMessage}</p>
        )}
      </div>

      <div className="flex-shrink-0 ml-1">
        {file.status === 'completed' && (
          <span className="inline-flex items-center gap-1">
            {warningsTitle && (
              <span title={warningsTitle} aria-label={warningsTitle}>
                <AlertTriangle size={14} className="text-text-tertiary" />
              </span>
            )}
            <CheckCircle size={16} className="text-success" />
          </span>
        )}
        {file.status === 'error' && <XCircle size={16} className="text-error" />}
      </div>
    </div>
  );
}
