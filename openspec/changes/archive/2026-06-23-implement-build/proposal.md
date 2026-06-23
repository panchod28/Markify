## Why

Markify necesita build scripts (PyInstaller para sidecar), configuraciones de Vite/TypeScript, tests del sidecar, y un `package.json` completo con scripts y dependencias correctas. Es el paso final del orden de implementación y une todas las piezas: frontend, backend Rust y sidecar Python en un proceso de build unificado.

## What Changes

- Crear `sidecar/build.py` — script PyInstaller con detección de target triple
- Crear `sidecar/tests/test_sanitizer.py` y `test_protocol.py` — tests unitarios
- Actualizar `package.json` con scripts completos (`dev`, `build`, `build:sidecar`, `build:all`, `lint`, `type-check`, `test`)
- Crear/actualizar `vite.config.ts` con alias `@/` y puerto 1420
- Crear/actualizar `tsconfig.json` con paths y strict mode
- Verificar que la estructura del proyecto coincide con el spec

## Capabilities

### New Capabilities

- `build-sidecar`: Script PyInstaller con detección de plataforma, exclusión de módulos pesados
- `build-config`: Configuraciones de Vite, TypeScript y package.json para el build unificado
- `sidecar-tests`: Tests unitarios para sanitizer y protocol con pytest

### Modified Capabilities

N/A.

## Impact

- **Crea:** `sidecar/build.py`, `sidecar/tests/test_sanitizer.py`, `sidecar/tests/test_protocol.py`
- **Modifica:** `package.json`, `vite.config.ts`, `tsconfig.json`
