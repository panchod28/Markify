import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileText, FileX } from 'lucide-react';
import { cn } from '@/lib/cn';
import type { PreviewViewMode } from '@/types';

interface PreviewPanelProps {
  content: string | null;
  viewMode: PreviewViewMode;
  onToggleViewMode: () => void;
  allFailed?: boolean;
}

export function PreviewPanel({ content, viewMode, onToggleViewMode, allFailed = false }: PreviewPanelProps) {
  const { t } = useTranslation();

  const MAX_PREVIEW_CHARS = 50_000;
  const isTruncated = content !== null && content.length > MAX_PREVIEW_CHARS;
  const displayContent = isTruncated ? content.slice(0, MAX_PREVIEW_CHARS) : content;

  if (allFailed) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-text-tertiary">
        <FileX size={48} className="opacity-30 text-error" />
        <p className="text-sm">{t('results.allFailedTitle')}</p>
        <p className="text-xs opacity-70">{t('results.allFailedDescription')}</p>
      </div>
    );
  }

  if (content === null) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-text-tertiary">
        <FileText size={48} className="opacity-30" />
        <p className="text-sm">{t('preview.selectFile')}</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface">
        <span className="text-xs text-text-tertiary">{t('preview.rendered')}</span>
        <div className="flex gap-1">
          <button
            onClick={onToggleViewMode}
            className={cn(
              'px-2 py-1 text-xs font-medium rounded-md transition-colors',
              viewMode === 'rendered'
                ? 'bg-accent-subtle text-accent'
                : 'text-text-secondary hover:text-text-primary',
            )}
          >
            {t('preview.rendered')}
          </button>
          <button
            onClick={onToggleViewMode}
            className={cn(
              'px-2 py-1 text-xs font-medium rounded-md transition-colors',
              viewMode === 'raw'
                ? 'bg-accent-subtle text-accent'
                : 'text-text-secondary hover:text-text-primary',
            )}
          >
            {t('preview.raw')}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {isTruncated && (
          <div className="mb-4 px-3 py-2 rounded-md bg-surface-secondary border border-border text-xs text-text-secondary">
            ⚠️ Archivo grande — mostrando los primeros {MAX_PREVIEW_CHARS.toLocaleString()} caracteres de {content!.length.toLocaleString()} totales.
          </div>
        )}
        {viewMode === 'rendered' ? (
          <div className="markdown-preview">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent!}</ReactMarkdown>
          </div>
        ) : (
          <pre className="text-sm font-mono text-text-primary whitespace-pre-wrap">
            <code>{displayContent}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
