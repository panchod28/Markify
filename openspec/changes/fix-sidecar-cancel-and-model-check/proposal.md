## Why

Probando la build `--onedir` desde la UI (macOS, 2026-10-17) aparecieron dos fallos que ya existen en `main` y que afectan a quien usa audio:

1. **El modal de descarga de Whisper sale siempre**, aunque el modelo ya esté en disco (y se vuelve a descargar 145 MB). Causa: el sidecar responde `check_model` con `model_status` **sin `request_id`**, y Rust solo resuelve la comprobación si lo recibe; `check_whisper_model` siempre expira, y además `resetToEmpty` reinicia `whisperModelAvailable` a `false`.
2. **Cancelar no cancela una conversión en curso**: el bucle de `main.py` lee `cancel` de stdin solo cuando `handle_convert` termina. Al cancelar un audio de 113 s la UI quedó en "Cancelando…" ~2 min y terminó como "1 archivo convertido correctamente". Además Whisper hace una única llamada bloqueante, así que aunque el `cancel` se leyera a tiempo nadie lo consulta hasta el final.

## What Changes

- **Sidecar**: un hilo lector de stdin atiende `cancel` y `check_model` al instante y encola `convert`/`download_model` para un único trabajador; `write_message` pasa a ser seguro entre hilos; `model_status` incluye `request_id`.
- **Whisper**: la transcripción pasa a ser cancelable entre ventanas de ~30 s y emite progreso real (hoy: 0 % → 50 % simulado → 100 %), enganchando la barra de progreso interna de `whisper.transcribe`.
- **Frontend**: `resetToEmpty` conserva el estado del modelo Whisper; el modal solo aparece si el modelo realmente falta.
- **Pruebas**: despacho sin torch (módulo nuevo `dispatcher.py` testeable), prueba de concurrencia de escritura, prueba del *shim* de progreso, `smoke_test.py` comprueba `request_id`.
- **Docs**: spec `05-sidecar-protocol` (hilos, `request_id`, semántica de cancelación).

Sin cambios **BREAKING**: los mensajes existentes no cambian; solo se añade `request_id` a `model_status` y progreso más fino en `file_progress`. Rust no cambia.

## Capabilities

### New Capabilities

- `sidecar-request-handling`: lectura de comandos desacoplada de la ejecución (lector + trabajador), `cancel` y `check_model` inmediatos, correlación por `request_id`, escritura segura entre hilos, apagado limpio en EOF.
- `whisper-cancel-progress`: cancelación y progreso real de la transcripción mediante el hook de progreso de Whisper, con degradación si la API interna cambia.
- `model-availability-ui`: disponibilidad del modelo Whisper en el store (comprobación al abrir, conservada entre conversiones, modal solo si falta).

### Modified Capabilities

<!-- Ninguna en formato OpenSpec; los specs vigentes son .md planos (05-sidecar-protocol, 03-stores, 09-pipeline).
     Al archivar hay que reflejar los cambios en 05 y 03 (ver tasks.md, grupo 6). -->

## Impact

- **Sidecar**: `main.py` (bucle), `protocol.py` (lock), `whisper_handler.py` (hook y cancelación), nuevo `dispatcher.py`, tests nuevos en `sidecar/tests/`, `smoke_test.py`, `requirements.txt` (acotar versión de `openai-whisper`).
- **Frontend**: `useConversionStore.resetToEmpty` (y su test).
- **Rust / protocolo hacia el frontend**: sin cambios.
- **Relación**: independiente de `sidecar-onedir` y de `add-ocr-image-pdf-support`; este último reutiliza `cancel_flag` y se beneficia del mismo despacho (OCR por página cancelable de inmediato).
