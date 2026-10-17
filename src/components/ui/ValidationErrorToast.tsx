import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { LEGACY_REPLACEMENT } from '@/types';
import type { LegacyExtension } from '@/types';
import type { FileValidationError } from '@/stores/useConversionStore';

interface ValidationErrorToastProps {
  errors: FileValidationError[];
  onDismiss: () => void;
}

export function ValidationErrorToast({ errors, onDismiss }: ValidationErrorToastProps) {
  const { t } = useTranslation();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (errors.length > 0) {
      timerRef.current = setTimeout(onDismiss, 5000);
      return () => {
        if (timerRef.current) clearTimeout(timerRef.current);
      };
    }
  }, [errors.length, onDismiss]);

  if (errors.length === 0) return null;

  const shownErrors = errors.slice(0, 3);
  const remaining = errors.length - 3;

  const formatError = (error: FileValidationError): string => {
    switch (error.type) {
      case 'unsupported':
        return t('errors.unsupportedFormat', { ext: error.ext });
      case 'legacy_format':
        return t('errors.legacyFormat', { ext: error.ext, modern: LEGACY_REPLACEMENT[error.ext as LegacyExtension] });
      case 'too_large':
        return t('errors.fileTooBig', { filename: error.filename });
      case 'batch_too_large':
        return t('errors.batchTooBig');
      case 'too_many_files':
        return t('errors.tooManyFiles', { count: 50 });
      case 'duplicate':
        return t('errors.duplicate', { filename: error.filename });
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 16 }}
        className="fixed bottom-4 right-4 z-50 max-w-[320px] bg-surface-elevated border-l-[3px] border-l-error border border-border rounded-lg shadow-lg p-4"
      >
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            {shownErrors.map((error, i) => (
              <p key={i} className="text-sm text-error">
                {formatError(error)}
              </p>
            ))}
            {remaining > 0 && (
              <p className="text-xs text-text-tertiary mt-1">
                {t('errors.moreErrors', { count: remaining })}
              </p>
            )}
          </div>
          <button onClick={onDismiss} className="flex-shrink-0 text-text-tertiary hover:text-text-primary">
            <X size={14} />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
