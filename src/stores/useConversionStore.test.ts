import { beforeEach, describe, expect, it } from 'vitest';
import { useConversionStore } from './useConversionStore';
import type { ConversionFile } from '@/types';

const file: ConversionFile = {
  id: '1',
  originalName: 'a.mp3',
  sanitizedName: 'a.md',
  path: '/tmp/a.mp3',
  sizeBytes: 1,
  formattedSize: '1 B',
  category: 'audio',
  extension: 'mp3',
  status: 'completed',
  progress: 100,
};

describe('useConversionStore.resetToEmpty', () => {
  beforeEach(() => {
    useConversionStore.getState().resetToEmpty();
    useConversionStore.setState({
      whisperModelAvailable: false,
      whisperModelDownloading: false,
      whisperModelDownloadProgress: 0,
    });
  });

  it('clears files and state of the conversion', () => {
    useConversionStore.setState({ files: [file], appState: 'results', isCancelling: true });
    useConversionStore.getState().resetToEmpty();
    const s = useConversionStore.getState();
    expect(s.files).toEqual([]);
    expect(s.appState).toBe('empty');
    expect(s.isCancelling).toBe(false);
  });

  it('keeps the Whisper model state so "Nueva conversión" does not ask for the download again', () => {
    useConversionStore.setState({
      files: [file],
      whisperModelAvailable: true,
      whisperModelDownloadProgress: 100,
      whisperModelDownloadedMB: 145,
    });
    useConversionStore.getState().resetToEmpty();
    const s = useConversionStore.getState();
    expect(s.whisperModelAvailable).toBe(true);
    expect(s.whisperModelDownloadProgress).toBe(100);
    expect(s.whisperModelDownloadedMB).toBe(145);
    expect(s.files).toEqual([]);
  });
});

describe('useConversionStore._handleFileUpdate', () => {
  it('copies the optional warnings of a completed file and leaves files without them untouched', () => {
    const base = { ...file, status: 'processing' as const, progress: 0 };
    useConversionStore.setState({ files: [base, { ...base, id: '2' }] });
    const warnings = [{ page: null, stage: 'layout', code: 'low_confidence_dropped', message: 'Se omitieron 6 líneas' }];
    useConversionStore.getState()._handleFileUpdate({
      fileId: '1', status: 'completed', progress: 100, markdownContent: 'texto', warnings,
    });
    const [a, b] = useConversionStore.getState().files;
    expect(a.warnings).toEqual(warnings);
    expect(a.status).toBe('completed');
    expect(b.warnings).toBeUndefined();
  });
});


describe('useConversionStore.addFiles validation of legacy Office formats', () => {
  beforeEach(() => useConversionStore.getState().resetToEmpty());

  const make = (name: string) => new File(['x'], name);

  it('rejects .doc and .ppt with their own error and keeps the rest of the batch', () => {
    useConversionStore.getState().addFiles([make('informe.doc'), make('informe.docx'), make('charla.ppt'), make('datos.xyz')]);
    const s = useConversionStore.getState();
    expect(s.files.map(f => f.originalName)).toEqual(['informe.docx']);
    expect(s.validationErrors).toEqual([
      { type: 'legacy_format', filename: 'informe.doc', ext: 'doc' },
      { type: 'legacy_format', filename: 'charla.ppt', ext: 'ppt' },
      { type: 'unsupported', filename: 'datos.xyz', ext: 'xyz' },
    ]);
  });

  it('still accepts .xls', () => {
    useConversionStore.getState().addFiles([make('hoja.xls')]);
    expect(useConversionStore.getState().files.map(f => f.extension)).toEqual(['xls']);
  });
});
