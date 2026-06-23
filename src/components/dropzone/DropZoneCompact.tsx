import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { open } from '@tauri-apps/plugin-dialog';
import { Plus } from 'lucide-react';
import { useConversionStore } from '@/stores/useConversionStore';
import { SUPPORTED_EXTENSIONS } from '@/types';

const DIALOG_EXTENSIONS: string[] = [...SUPPORTED_EXTENSIONS] as string[];

export function DropZoneCompact() {
  const { t } = useTranslation();
  const [isDragActive, setIsDragActive] = useState(false);

  // Visual drag state only — AppShell handles the actual drop globally
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  };
  const handleDragLeave = () => setIsDragActive(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    // AppShell's onDragDropEvent handles the actual file paths
  };

  const handleClick = async () => {
    const selected = await open({
      multiple: true,
      filters: [{ name: 'Archivos soportados', extensions: DIALOG_EXTENSIONS }],
    });
    if (selected) {
      const paths = Array.isArray(selected) ? selected : [selected];
      useConversionStore.getState().addFilePaths(paths);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`flex items-center gap-2 h-10 px-3 rounded-md border border-dashed transition-colors cursor-pointer \${
        isDragActive
          ? 'border-solid border-[var(--color-dropzone-border-active)] bg-[var(--color-dropzone-bg-active)]'
          : 'border-border hover:border-border-strong hover:bg-surface-secondary'
      }`}
    >
      <Plus size={16} className="text-text-tertiary" />
      <span className="text-sm text-text-secondary">
        {isDragActive ? t('dropzone.dragActive') : t('fileList.addMore')}
      </span>
    </div>
  );
}
