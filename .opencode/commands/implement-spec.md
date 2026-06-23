# implement-spec

Implementa una spec específica de Markify de principio a fin.

## Uso
```
/implement-spec <número>
```
Ejemplo: `/implement-spec 03` implementa la spec de Zustand stores.

## Instrucciones

1. **Lee la spec primero**: abre `openspec/specs/0$ARGUMENTS-*.md` y léela COMPLETA antes de escribir una sola línea de código.

2. **Lee las dependencias**: revisa qué otras specs debe conocer (indicado al inicio de cada spec con "Dependencias").

3. **Implementa en orden**: respeta el orden exacto que indica la spec. No saltes pasos.

4. **Sin creatividad no pedida**: implementa EXACTAMENTE lo que dice la spec. Si algo es ambiguo, pregunta antes de asumir.

5. **Verifica al final**:
   - TypeScript sin errores: `npx tsc --noEmit`
   - Imports correctos (sin imports circulares)
   - Nombres de archivos exactos como indica la spec

## Specs disponibles
| # | Spec | Archivos destino |
|---|------|-----------------|
| 01 | types | `src/types/index.ts` |
| 02 | design-system | `src/index.css`, `tailwind.config.js`, `components.json` |
| 03 | stores | `src/stores/useAppStore.ts`, `useConversionStore.ts`, `usePreviewStore.ts` |
| 04 | tauri-commands | `src-tauri/src/lib.rs`, `Cargo.toml` |
| 05 | sidecar-protocol | `sidecar/main.py`, `protocol.py`, `converter.py`, `whisper_handler.py`, `model_manager.py`, `error_messages.py` |
| 06 | components | `src/components/**/*.tsx` (23 componentes) |
| 07 | screens | `src/App.tsx` + ajustes de layout |
| 08 | i18n | `src/i18n/index.ts` + JSONs ES/EN |
| 09 | pipeline | Lógica end-to-end — revisar stores + sidecar |
| 10 | build | `sidecar/build.py`, `sidecar/requirements.txt`, scripts de build |

## Regla de oro
Si la spec dice algo diferente a lo que ya existe en el código, **la spec gana**.
