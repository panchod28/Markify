## Why

Markify necesita el proceso Python sidecar que convierte documentos y transcribe audio. Los comandos Rust (spec 04) ya escriben mensajes JSON al stdin del sidecar y esperan respuestas por stdout, pero el sidecar aún no existe. Sin este componente, la app no puede ejecutar ninguna conversión real.

## What Changes

- Crear `sidecar/` con 8 archivos Python que implementan el protocolo stdin/stdout JSON newline-delimited
- `main.py` — entry point, loop de lectura, despacho de comandos (`convert`, `cancel`, `check_model`, `download_model`)
- `protocol.py` — `read_message()` / `write_message()` con flush obligatorio
- `converter.py` — conversión de documentos vía `markitdown`, con manejo de errores (password, corrupto, vacío)
- `whisper_handler.py` — transcripción de audio vía `openai-whisper`, con cancel_flag y progreso
- `model_manager.py` — verificación y descarga del modelo Whisper base (145 MB), progreso callback
- `sanitizer.py` — sanitización de nombres de archivo
- `error_messages.py` — mapeo de excepciones a mensajes ES/EN
- `requirements.txt` — dependencias (markitdown, openai-whisper, torch+cpu, PyInstaller)

## Capabilities

### New Capabilities

- `sidecar-main`: Entry point y loop principal del sidecar con despacho de comandos y manejo de cancelación
- `sidecar-protocol`: Lectura/escritura JSON newline-delimited por stdin/stdout
- `sidecar-converter`: Conversión de documentos a Markdown con markitdown
- `sidecar-whisper`: Transcripción de audio a Markdown con Whisper + cancelación
- `sidecar-model`: Gestión de descarga/verificación del modelo Whisper
- `sidecar-errors`: Mapeo de excepciones Python a mensajes de usuario localizados

### Modified Capabilities

N/A.

## Impact

- **Crea**: `sidecar/main.py`, `sidecar/protocol.py`, `sidecar/converter.py`, `sidecar/whisper_handler.py`, `sidecar/model_manager.py`, `sidecar/sanitizer.py`, `sidecar/error_messages.py`, `sidecar/requirements.txt`
- **Dependencias Python**: `markitdown`, `openai-whisper`, `torch` (CPU), `PyInstaller`
- **Tauri sidecar**: El binario `markify-sidecar` se empaqueta con PyInstaller (spec 10-build). El placeholder actual en `src-tauri/binaries/` se reemplazará.
