import { describe, expect, it } from 'vitest';
import { getExtension, getFileCategory, isSupportedExtension } from './fileUtils';

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

  it('rejects unsupported extensions', () => {
    expect(getFileCategory('gif')).toBeNull();
    expect(getFileCategory('heic')).toBeNull();
    expect(isSupportedExtension('exe')).toBe(false);
  });

  it('is case-insensitive through getExtension', () => {
    expect(getFileCategory(getExtension('Captura.PNG'))).toBe('image');
  });
});
