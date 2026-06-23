import { ResultsSidebar } from './ResultsSidebar';
import { PreviewPanel } from './PreviewPanel';
import { ResultsActionBar } from './ResultsActionBar';
import type { ConversionFile, ConversionSummary, PreviewViewMode } from '@/types';

interface ResultsViewProps {
  files: ConversionFile[];
  summary: ConversionSummary;
  selectedFileId: string | null;
  onSelectFile: (id: string) => void;
  onSave: () => Promise<void>;
  onRetryFailed: () => void;
  onNewConversion: () => void;
  viewMode: PreviewViewMode;
  onToggleViewMode: () => void;
  savedPath: string | null;
  onOpenInFolder: () => void;
}

export function ResultsView({
  files,
  summary,
  selectedFileId,
  onSelectFile,
  onSave,
  onRetryFailed,
  onNewConversion,
  viewMode,
  onToggleViewMode,
  savedPath,
  onOpenInFolder,
}: ResultsViewProps) {
  const selectedFile = files.find(f => f.id === selectedFileId);

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-1 overflow-hidden">
        <ResultsSidebar
          files={files}
          summary={summary}
          selectedFileId={selectedFileId}
          onSelectFile={onSelectFile}
        />
        <div className="flex-1 flex flex-col overflow-hidden">
          <PreviewPanel
            content={selectedFile?.markdownContent ?? null}
            viewMode={viewMode}
            onToggleViewMode={onToggleViewMode}
            allFailed={summary.completed === 0 && summary.failed > 0}
          />
        </div>
      </div>
      <ResultsActionBar
        summary={summary}
        savedPath={savedPath}
        onSave={onSave}
        onRetryFailed={onRetryFailed}
        onNewConversion={onNewConversion}
        onOpenInFolder={onOpenInFolder}
      />
    </div>
  );
}
