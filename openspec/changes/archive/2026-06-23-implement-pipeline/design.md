## Context

El pipeline de conversión ya está implementado en stores, sidecar, y App.tsx. La única pieza que necesita alinearse es `sanitizeFilename()` en TypeScript, que debe replicar exactamente el algoritmo Python de 10 pasos.

## Goals / Non-Goals

**Goals:**
- Actualizar `sanitizeFilename()` TS para usar NFKD, incluir dots en step 5, usar fallback `'archivo_sin_nombre'`
- Verificar que la tabla de ejemplos produce los resultados esperados

**Non-Goals:**
- Modificar el sidecar Python (ya está correcto)
- Cambiar la lógica de validación en stores (ya es correcta)
- Añadir paralelismo (v2)

## Decisions

1. **NFKD en lugar de NFD**: NFKD descompone ligaduras (ﬃ → ffi) además de acentos. Más completo para sanitización.
2. **Dots incluidos en step 5**: `file.with.dots.pdf` → `file_with_dots.md`. El spec lo requiere.
3. **Fallback `'archivo_sin_nombre'`**: Coincide con Python para consistencia.
