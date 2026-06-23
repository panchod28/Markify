import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  dismissLabel: string;
  variant?: 'default' | 'destructive';
  onConfirm: () => void;
  onDismiss: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  dismissLabel,
  variant = 'default',
  onConfirm,
  onDismiss,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onDismiss}>
      <DialogContent className="max-w-[380px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="flex gap-2 justify-end mt-4">
          <button
            onClick={onDismiss}
            className="h-9 px-4 text-sm font-medium text-text-secondary border border-border rounded-md hover:bg-surface-secondary transition-colors"
          >
            {dismissLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`h-9 px-4 text-sm font-semibold rounded-md transition-colors ${
              variant === 'destructive'
                ? 'bg-error hover:bg-error/90 text-white'
                : 'bg-accent hover:bg-accent-hover text-text-onaccent'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
