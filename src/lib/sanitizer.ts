export function sanitizeFilename(filename: string): string {
  // Step 1: Trim and extract stem (name without extension)
  let name = filename.trim().replace(/\.[^.]+$/, '');

  // Step 2: NFD normalization
  name = name.normalize('NFD');

  // Step 3: Remove non-ASCII (combining chars + other non-ASCII)
  name = name.replace(/[\u0300-\u036f]/g, '');
  name = name.replace(/[^\x00-\x7F]/g, '');

  // Step 4: Lowercase
  name = name.toLowerCase();

  // Step 5: Replace spaces, dashes with underscore
  name = name.replace(/[\s-]+/g, '_');

  // Step 6: Keep only alphanumeric, underscores, and dots
  name = name.replace(/[^a-z0-9_.]/g, '');

  // Step 7: Replace dots with underscore
  name = name.replace(/\./g, '_');

  // Step 8: Collapse consecutive underscores
  name = name.replace(/_+/g, '_');

  // Step 9: Trim underscores and dots from start and end
  name = name.replace(/^[_.]+|[_.]+$/g, '');

  // Fallback if empty
  if (!name) {
    name = 'archivo_sin_nombre';
  }

  // Step 10: Add .md extension
  return `${name}.md`;
}
