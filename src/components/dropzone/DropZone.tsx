import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { FileUp } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import { SUPPORTED_EXTENSIONS } from '@/types';
import { useConversionStore } from '@/stores/useConversionStore';

const DIALOG_EXTENSIONS: string[] = [...SUPPORTED_EXTENSIONS] as string[];

export function DropZone() {
  const { t } = useTranslation();
  const [isDragActive, setIsDragActive] = useState(false);

  useEffect(() => {
    let unlisten: (() => void) | undefined;

    import('@tauri-apps/api/webview').then(({ getCurrentWebview }) => {
    getCurrentWebview().onDragDropEvent((event: { payload: { type: string } }) => {
      const { type } = event.payload;
      if (type === 'enter') setIsDragActive(true);
      else if (type === 'leave' || type === 'drop') setIsDragActive(false);
    }).then((fn: () => void) => { unlisten = fn; });
    });
    return () => { unlisten?.(); };
  }, []);

  const handleSelectFiles = async () => {
    const selected = await open({
      multiple: true,
      filters: [{
        name: t('dropzone.dialogFilter'),
        extensions: DIALOG_EXTENSIONS,
      }],
    });

    if (selected) {
      const paths = Array.isArray(selected) ? selected : [selected];
      useConversionStore.getState().addFilePaths(paths);
    }
  };

  return (
    <div
      className={`
        flex flex-col items-center justify-center
        w-full max-w-[560px] mx-auto
        rounded-lg border-2 border-dashed px-8 py-12
        transition-all duration-[150ms] cursor-default select-none
        ${isDragActive
          ? 'border-solid border-[var(--color-dropzone-border-active)] bg-[var(--color-dropzone-bg-active)]'
          : 'border-[var(--color-dropzone-border)] bg-[var(--color-dropzone-bg)]'
        }
      `}
    >
      <motion.div
        animate={{ scale: isDragActive ? 1.1 : 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      >
        <FileUp size={64} className="text-accent opacity-60 mb-4" />
      </motion.div>

      <h2 className="text-2xl font-semibold text-text-primary mb-2">
        {isDragActive ? t('dropzone.dragActive') : t('dropzone.title')}
      </h2>
      <p className="text-sm text-text-secondary mb-6">
        {t('dropzone.subtitle')}
      </p>

      {!isDragActive && (
        <button
          type="button"
          onClick={handleSelectFiles}
          className="px-4 py-2 text-sm font-medium text-accent rounded-md hover:bg-accent-subtle transition-colors"
        >
          {t('fileList.selectFiles')}
        </button>
      )}

      <p className="text-xs text-text-tertiary mt-4">
        {t('dropzone.supported')}
      </p>
    </div>
  );
}
