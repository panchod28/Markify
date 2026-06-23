## Why

El pipeline end-to-end define cómo se mueven los archivos desde el dropzone hasta el archivo guardado en disco. La mayoría de la implementación ya existe (validación en stores, conversión en sidecar, cancelación), pero la función `sanitizeFilename()` en el frontend necesita alinearse con el algoritmo de 10 pasos del spec, y el orden de validaciones debe verificarse.

## What Changes

- Actualizar `src/lib/sanitizer.ts` con el algoritmo completo de 10 pasos según spec (NFKD, dots en step 5, fallback 'archivo_sin_nombre')
- Verificar que el orden de validaciones en `useConversionStore.addFiles()` coincida con el spec: too_many_files para todo, resto por archivo
- Documentar que el pipeline ya está implementado en stores + sidecar + App.tsx

## Capabilities

### New Capabilities

- `pipeline-sanitizer`: Algoritmo de sanitización completo de 10 pasos en TypeScript, sincronizado con Python

### Modified Capabilities

N/A — el pipeline ya está implementado, solo se refina la sanitización.

## Impact

- **Modifica:** `src/lib/sanitizer.ts`
- **Verifica:** `src/stores/useConversionStore.ts` (orden de validaciones)
