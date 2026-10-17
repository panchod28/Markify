import { DOCUMENT_EXTENSIONS, AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, LEGACY_EXTENSIONS, SUPPORTED_EXTENSIONS } from '@/types';
import type { FileCategory, LegacyExtension, SupportedExtension } from '@/types';

export function getExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() ?? '';
}

export function isSupportedExtension(ext: string): ext is SupportedExtension {
  return (SUPPORTED_EXTENSIONS as readonly string[]).includes(ext);
}

export function isLegacyExtension(ext: string): ext is LegacyExtension {
  return (LEGACY_EXTENSIONS as readonly string[]).includes(ext);
}

export function getFileCategory(ext: string): FileCategory | null {
  if ((DOCUMENT_EXTENSIONS as readonly string[]).includes(ext)) return 'document';
  if ((AUDIO_EXTENSIONS as readonly string[]).includes(ext)) return 'audio';
  if ((IMAGE_EXTENSIONS as readonly string[]).includes(ext)) return 'image';
  return null;
}
