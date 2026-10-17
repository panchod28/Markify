import { describe, expect, it } from 'vitest';
import { toRenderedMarkdown } from './markdownPreview';

describe('toRenderedMarkdown', () => {
  it('turns slide markers into horizontal rules (not at the very start)', () => {
    const md = '<!-- Slide number: 1 -->\n# Uno\nTexto\n\n<!-- Slide number: 2 -->\n# Dos';
    expect(toRenderedMarkdown(md)).toBe('# Uno\nTexto\n\n\n\n---\n\n\n# Dos');
  });

  it('keeps a text line followed by a marker out of a setext heading', () => {
    expect(toRenderedMarkdown('Texto\n<!-- Slide number: 2 -->\n# Dos')).toContain('Texto\n\n\n---\n\n');
  });

  it('hides the page-failure markers and any other HTML comment', () => {
    const md = 'Antes\n\n<!-- Markify: página 2 no se pudo procesar (page_render_failed) -->\n\nDespués <!-- nota --> fin';
    expect(toRenderedMarkdown(md)).toBe('Antes\n\n\n\nDespués  fin');
  });

  it('drops a comment cut by the preview size limit', () => {
    expect(toRenderedMarkdown('Texto <!-- Markify: pági')).toBe('Texto ');
  });

  it('leaves ordinary Markdown untouched', () => {
    const md = '# Título\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\n*cursiva* y --- en medio';
    expect(toRenderedMarkdown(md)).toBe(md);
  });
});
