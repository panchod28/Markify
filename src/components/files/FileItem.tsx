import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';
import { FileIcon } from './FileIcon';
import type { ConversionFile } from '@/types';

interface FileItemProps {
  file: ConversionFile;
  onRemove: (id: string) => void;
}

export function FileItem({ file, onRemove }: FileItemProps) {
  const { t } = useTranslation();

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-3 px-4 py-2 h-16 rounded-md hover:bg-surface-secondary transition-colors duration-[100ms] group"
    >
      <div className="flex-shrink-0">
        <FileIcon extension={file.extension} size={32} />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-base font-medium text-text-primary truncate">
          {file.originalName}
        </p>
        <p className="text-xs text-text-secondary truncate">
          {file.sanitizedName}
          <span className="mx-2">·</span>
          {file.formattedSize}
        </p>
      </div>

      <button
        onClick={() => onRemove(file.id)}
        className="opacity-0 group-hover:opacity-100 flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-md text-text-tertiary hover:text-error hover:bg-error-subtle transition-all duration-[100ms]"
        aria-label={t('fileList.removeFile')}
      >
        <X size={16} />
      </button>
    </motion.div>
  );
}
