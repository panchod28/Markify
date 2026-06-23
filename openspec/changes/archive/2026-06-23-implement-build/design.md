## Context

El spec 10 define la build final: PyInstaller para el sidecar, Vite/TypeScript config para el frontend, y tests del sidecar. Es el último paso para tener el proyecto listo para distribución.

## Goals / Non-Goals

**Goals:**
- Script PyInstaller que detecta plataforma y genera binario en `src-tauri/binaries/`
- Configs Vite y TypeScript correctas con aliases
- Tests unitarios para sanitizer y protocol

**Non-Goals:**
- Generar binarios reales (requiere instalar dependencias Python)
- Crear fixtures de test (PDFs, etc.)
- Firmar binarios para distribución

## Decisions

1. **`--onefile` PyInstaller**: Un solo binario por plataforma. El modelo Whisper se descarga on-demand.

2. **Excluir módulos pesados (`matplotlib`, `PIL`, `tkinter`)**: Reduce tamaño del binario de ~300MB a ~100MB.

3. **`--console` flag**: El sidecar es CLI, no GUI. Necesario para stdin/stdout.

4. **Port 1420 en Vite**: Coincide con `tauri.conf.json` `devUrl`.
