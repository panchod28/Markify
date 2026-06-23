import { FileText, FileCode, Sheet, Presentation, Music, Video } from 'lucide-react';
import { FILE_ICON_MAP } from '@/types';
import type { SupportedExtension } from '@/types';

interface FileIconProps {
  extension: string;
  size?: number;
  className?: string;
}

const ICON_COMPONENTS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  FileText,
  FileCode,
  Sheet,
  Presentation,
  Music,
  Video,
};

export function FileIcon({ extension, size = 24, className = '' }: FileIconProps) {
  const entry = FILE_ICON_MAP[extension as SupportedExtension];

  if (!entry) {
    return <FileText size={size} className={`text-gray-400 ${className}`} />;
  }

  const IconComponent = ICON_COMPONENTS[entry.icon] ?? FileText;
  return <IconComponent size={size} className={`${entry.colorClass} ${className}`} />;
}
