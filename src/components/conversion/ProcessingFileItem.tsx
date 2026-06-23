import { FileIcon } from '@/components/files/FileIcon';
import { StatusBadge } from './StatusBadge';
import { ProgressBar } from './ProgressBar';
import type { ConversionFile } from '@/types';

interface ProcessingFileItemProps {
  file: ConversionFile;
}

export function ProcessingFileItem({ file }: ProcessingFileItemProps) {
  const isCompleted = file.status === 'completed';

  return (
    <div className={`flex flex-col gap-1.5 px-4 py-3 ${isCompleted ? 'opacity-70' : ''}`}>
      <div className="flex items-center gap-3">
        <FileIcon extension={file.extension} size={24} />

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text-primary truncate">
            {file.originalName}
          </p>
          {file.status === 'error' && file.errorMessage && (
            <p className="text-xs text-error mt-0.5">{file.errorMessage}</p>
          )}
        </div>

        <StatusBadge status={file.status} />
      </div>

      <ProgressBar progress={file.progress} status={file.status} className="mt-1" />
    </div>
  );
}
