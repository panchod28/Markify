import { useTranslation } from 'react-i18next';
import { Clock, CheckCircle, XCircle } from 'lucide-react';
import type { FileStatus } from '@/types';

interface StatusBadgeProps {
  status: FileStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useTranslation();

  switch (status) {
    case 'pending':
      return (
        <span className="inline-flex items-center gap-1 h-6 px-2 rounded-sm bg-surface-secondary text-text-tertiary text-xs font-medium">
          <Clock size={14} />
          {t('processing.status.pending')}
        </span>
      );
    case 'processing':
      return (
        <span className="inline-flex items-center gap-1 h-6 px-2 rounded-sm bg-accent-subtle text-accent text-xs font-medium">
          <svg className="animate-spin" width="14" height="14" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="25" strokeDashoffset="10" />
          </svg>
          {t('processing.status.processing')}
        </span>
      );
    case 'completed':
      return (
        <span className="inline-flex items-center gap-1 h-6 px-2 rounded-sm bg-success-subtle text-success text-xs font-medium">
          <CheckCircle size={14} />
          {t('processing.status.completed')}
        </span>
      );
    case 'error':
      return (
        <span className="inline-flex items-center gap-1 h-6 px-2 rounded-sm bg-error-subtle text-error text-xs font-medium">
          <XCircle size={14} />
          {t('processing.status.error')}
        </span>
      );
  }
}
