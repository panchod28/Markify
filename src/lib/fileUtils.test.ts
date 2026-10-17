import { describe, expect, it } from 'vitest';
import { getExtension, getFileCategory, isLegacyExtension, isSupportedExtension } from './fileUtils';

describe('getFileCategory', () => {
  it('keeps the existing categories', () => {
    for (const ext of ['pdf', 'docx', 'pptx', 'xlsx', 'html', 'csv']) expect(getFileCategory(ext)).toBe('document');
    for (const ext of ['mp3', 'mp4', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'aac']) expect(getFileCategory(ext)).toBe('audio');
  });

  it('categorizes images for OCR', () => {
    for (const ext of ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tif', 'tiff']) {
      expect(getFileCategory(ext)).toBe('image');
      expect(isSupportedExtension(ext)).toBe(true);
    }
  });

  it('keeps accepting the modern Office formats and old Excel', () => {
    for (const ext of ['docx', 'pptx', 'xlsx', 'xls']) expect(isSupportedExtension(ext)).toBe(true);
  });

  it('treats .doc and .ppt as legacy, not as supported', () => {
    for (const ext of ['doc', 'ppt']) {
      expect(isLegacyExtension(ext)).toBe(true);
      expect(isSupportedExtension(ext)).toBe(false);
      expect(getFileCategory(ext)).toBeNull();
    }
    for (const ext of ['docx', 'pptx', 'xls', 'xyz']) expect(isLegacyExtension(ext)).toBe(false);
  });

  it('rejects unsupported extensions', () => {
    expect(getFileCategory('gif')).toBeNull();
    expect(getFileCategory('heic')).toBeNull();
    expect(isSupportedExtension('exe')).toBe(false);
  });

  it('is case-insensitive through getExtension', () => {
    expect(getFileCategory(getExtension('Captura.PNG'))).toBe('image');
  });
});
