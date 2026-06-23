import { FileIcon } from '@/components/files/FileIcon';
import { CheckCircle, XCircle } from 'lucide-react';
import type { ConversionFile } from '@/types';

interface ResultFileItemProps {
  file: ConversionFile;
  isSelected: boolean;
  onClick: () => void;
}

export function ResultFileItem({ file, isSelected, onClick }: ResultFileItemProps) {
  const isClickable = file.status === 'completed';

  return (
    <div
      onClick={isClickable ? onClick : undefined}
      className={`
        flex items-center gap-3 px-4 py-3 cursor-default
        ${isClickable ? 'cursor-pointer hover:bg-surface-secondary' : ''}
        ${isSelected ? 'bg-accent-subtle border-l-[3px] border-l-accent' : 'border-l-[3px] border-l-transparent'}
        transition-colors duration-[100ms]
      `}
    >
      <FileIcon extension={file.extension} size={20} />

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary truncate">
          {file.originalName}
        </p>
        {file.status === 'error' && file.errorMessage && (
          <p className="text-xs text-error mt-0.5 truncate">{file.errorMessage}</p>
        )}
      </div>

      {file.status === 'completed' && <CheckCircle size={16} className="text-success flex-shrink-0" />}
      {file.status === 'error' && <XCircle size={16} className="text-error flex-shrink-0" />}
    </div>
  );
}
