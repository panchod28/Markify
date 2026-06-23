import { cn } from '@/lib/cn';
import type { FileStatus } from '@/types';

interface ProgressBarProps {
  progress: number;
  status: FileStatus;
  className?: string;
}

export function ProgressBar({ progress, status, className }: ProgressBarProps) {
  return (
    <div className={cn('h-1 rounded-sm bg-border overflow-hidden', className)}>
      <div
        className={cn('h-full rounded-sm transition-all', {
          'progress-shimmer w-full': status === 'processing' && progress === 0,
          'bg-accent': status === 'processing' && progress > 0,
          'bg-success w-full': status === 'completed',
          'bg-error w-full': status === 'error',
          'w-0': status === 'pending',
        })}
        style={
          status === 'processing' && progress > 0
            ? { width: `${progress}%`, transition: 'width 300ms ease-out' }
            : undefined
        }
      />
    </div>
  );
}
