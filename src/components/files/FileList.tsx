import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatePresence } from 'framer-motion';
import { ChevronRight } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileItem } from './FileItem';
import { DropZoneCompact } from '@/components/dropzone/DropZoneCompact';
import { ConfirmDialog } from '@/components/modals/ConfirmDialog';
import type { ConversionFile } from '@/types';

interface FileListProps {
  files: ConversionFile[];
  onRemove: (id: string) => void;
  onClearAll: () => void;
  onConvert: () => void;
  isConvertDisabled: boolean;
}

export function FileList({
  files,
  onRemove,
  onClearAll,
  onConvert,
  isConvertDisabled,
}: FileListProps) {
  const { t } = useTranslation();
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const handleClear = () => {
    if (files.length >= 3) {
      setShowClearConfirm(true);
    } else {
      onClearAll();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-semibold text-text-primary">
          {t('fileList.filesCount', { count: files.length })}
        </span>
        <button
          onClick={handleClear}
          className="px-2 py-1 text-sm font-medium text-error rounded-md hover:bg-error-subtle transition-colors"
        >
          {t('fileList.clearAll')}
        </button>
      </div>

      <ScrollArea className="flex-1">
        <AnimatePresence initial={false}>
          {files.map(file => (
            <FileItem key={file.id} file={file} onRemove={onRemove} />
          ))}
        </AnimatePresence>
      </ScrollArea>

      <div className="flex items-center justify-between px-4 py-3 border-t border-border">
        <DropZoneCompact />
        <button
          onClick={onConvert}
          disabled={isConvertDisabled}
          className="flex items-center gap-1 h-11 px-5 bg-accent hover:bg-accent-hover active:bg-accent-active text-text-onaccent font-semibold rounded-md disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-fast"
        >
          {t('fileList.convert')}
          <ChevronRight size={16} />
        </button>
      </div>

      <ConfirmDialog
        open={showClearConfirm}
        title={t('confirmDialog.clearAll.title')}
        description={t('confirmDialog.clearAll.description', { count: files.length })}
        confirmLabel={t('confirmDialog.clearAll.confirm')}
        dismissLabel={t('confirmDialog.clearAll.dismiss')}
        variant="destructive"
        onConfirm={() => {
          onClearAll();
          setShowClearConfirm(false);
        }}
        onDismiss={() => setShowClearConfirm(false)}
      />
    </div>
  );
}
