import { useTranslation } from 'react-i18next';
import type { ConversionSummary } from '@/types';

interface GlobalProgressProps {
  summary: ConversionSummary;
}

export function GlobalProgress({ summary }: GlobalProgressProps) {
  const { t } = useTranslation();

  return (
    <div className="px-4 py-3 flex items-center gap-2 border-b border-border" aria-live="polite">
      <svg className="animate-spin" width="14" height="14" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="25" strokeDashoffset="10" className="text-accent" />
      </svg>
      <span className="text-sm text-text-secondary">
        {t('processing.progress', { completed: summary.completed, total: summary.total })}
      </span>
    </div>
  );
}
